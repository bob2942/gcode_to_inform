#include <Arduino.h>
#include <FastAccelStepper.h>

#define STEPS_PER_REVOLUTION 3200 // steps/mm bei 16 microsteps und 1:1 Übersetzung
#define STEPS_PER_MM 224 // steps/mm
#define ACCEL 5000   // steps/s^2
#define MAX_RPM 414 // max RPM
#define MAX_SPEED STEPS_PER_REVOLUTION*MAX_RPM/60 //steps/s
//#define MAX_SPEED STEPS_PER_MM*100 // steps/s

//stepper pins
#define STEP_PIN 9
#define DIR_PIN 8
#define ENABLE_PIN 7

// stepper and heater power relay on pin D6

// define stepper direction
//#define FORWARD
#define BACKWARD

//variables for storing speed and flow. volatile because of use in interupt routine
volatile uint8_t speed = 0;
volatile float flow = 1.0; // extrusionsmultiplikator

//define Stepper
FastAccelStepperEngine engine = FastAccelStepperEngine();
FastAccelStepper *stepper = NULL;

inline void set_speed(){
  //Read out pins and store in variable with the positions D4|D3|A5|A4|A3|A2|A1|A0
  speed = (((PIND&((1<<PIND3)|(1<<PIND4)))<<3)|(PINC&((1<<PINC0)|(1<<PINC1)|(1<<PINC2)|(1<<PINC3)|(1<<PINC4)|(1<<PINC5)))); // read A0-A5
  speed ^= 0xFF; // invert values because octocupler inverts the signal
  speed = (int)speed*flow; // scale speed with flow
  speed = min(max(speed,0), 255); // limit speed to 0-255
  if(speed == 0){
    stepper->stopMove();      // stop the stepper if speed is 0
    PORTD |= (1<<DDD6);       // set D6 high to enable stepper and Heater Power
  }else if(speed == 255){
    stepper->stopMove();      // stop stepper if power off
    PORTD &= ~(1<<DDD6);      // set D6 low to disable stepper and Heater Power
  }else{
    PORTD |= (1<<DDD6);       // set D6 high to enable stepper and Heater Power
    stepper->setSpeedInHz((float)MAX_SPEED*(float)speed/(float)254); // steps/s
    #if defined(FORWARD)
      stepper->runForward();
    #elif defined(BACKWARD)
      stepper->runBackward();
    #endif
  }
}


// define pinchange interupt routines
ISR (PCINT2_vect){ // PCINT2_vect: interrupt vector for PORTD
  set_speed();
  //PCIFR |= (1<<PCIF1); // clear interuptflag for 
}

ISR (PCINT1_vect){ // PCINT1_vect: interrupt vector for PORTC
  set_speed();
}

void setup() {
  // initialise serial comunication
  Serial.begin(115200);

  DDRC &= ~((1<<DDC0)|(1<<DDC1)|(1<<DDC2)|(1<<DDC3)|(1<<DDC4)|(1<<DDC5)); //set pin A0-A5 als Input
  DDRD |= (1<<DDD6); //set pin D6 als Output
  DDRD &= ~((1<<DDD3)|(1<<DDD4)); //set pin D3 und D4 als Input

  //enable pinchange interupts for A0-A5,D3 and D4
  PCMSK1 |= (1<<PCINT8)|(1<<PCINT9)|(1<<PCINT10)|(1<<PCINT11)|(1<<PCINT12)|(1<<PCINT13);   
  PCMSK2 |= (1<<PCINT19)|(1<<PCINT20); 
  PCICR |= (1<<PCIE2)|(1<<PCIE1);
  //enable global interupts
  sei();

  // initalise stepper libary
  engine.init();
  stepper = engine.stepperConnectToPin(STEP_PIN);
  if (stepper) {
    stepper->setDirectionPin(DIR_PIN);
    stepper->setEnablePin(ENABLE_PIN);
    stepper->setAutoEnable(true);
    stepper->setAcceleration(ACCEL);    // steps/s²
    stepper->setSpeedInHz((float)MAX_SPEED*(float)speed/(float)255); // steps/s
  }
  PORTD |= (1<<DDD6); // set D6 high to enable stepper and Heater Power

  set_speed();
}




void loop() {

  // read in serial inputs to modify extrusionmultiplyer
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    if (input.length() > 0) {
      flow = input.toFloat();
      set_speed();
    }
  }

  //print out current state
  Serial.print("Speed: ");
  Serial.println(speed);
  Serial.print("Flow: ");
  Serial.println(flow);
  Serial.println("___________");
  delay(1000); // print every second
}
