#include <Arduino.h>
#include <FastAccelStepper.h>

#define STEPS_PER_REVOLUTION 3200 // steps/mm bei 16 microsteps und 1:1 Übersetzung
#define ACCEL 5000   // steps/s^2
#define MAX_RPM 414 // max RPM
#define MAX_SPEED STEPS_PER_REVOLUTION*MAX_RPM/60 //steps/s

//stepper pins
#define STEP_PIN 6
#define DIR_PIN 5
#define ENABLE_PIN 4

// stepper and heater power relay on pin D3


//#define FORWARD
#define BACKWARD


volatile uint8_t speed = 0;
volatile float set_massflow = 0;
volatile float flow = 1.0; // extrusionsmultiplikator

uint32_t time_now = 0;
uint32_t last_time = 0;

//define Stepper
FastAccelStepperEngine engine = FastAccelStepperEngine();
FastAccelStepper *stepper = NULL;

inline void set_speed(){
  speed = PINA;
  if(speed == 0){
    stepper->stopMove();      // stop the stepper if speed is 0
    PORTE |= (1<<PORTE5);     // set D3 high to enable stepper and Heater Power
  }else if(speed == 255){
    stepper->stopMove();      // stop stepper if power off
    PORTE &= ~(1<<PORTE5);     // set D3 low to disable stepper and Heater Power
  }else{
    PORTE |= (1<<PORTE5);     // set D3 high to enable stepper and Heater Power
    speed = (int)speed*flow; // scale speed with flow
    speed = min(max(speed,0), 255); // limit speed to 0-255
    stepper->setSpeedInHz((float)MAX_SPEED*(float)speed/(float)254); // steps/s
    #if defined(FORWARD)
      stepper->runForward();
    #elif defined(BACKWARD)
      stepper->runBackward();
    #endif
  }
}

void setup() {

  Serial.begin(115200);

  DDRA &= ~(0b11111111);  //set all pins as inputs
  DDRE |= (1<<DDE5);
  //enable global interupts
  sei();

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

  #if defined(FORWARD)
    stepper->runForward();
  #elif defined(BACKWARD)
    stepper->runBackward();
  #endif
}

void loop() {
  time_now = micros();
  set_speed();

  if(time_now-last_time >= 1000000){
    if (Serial.available()) {
      String i_s = Serial.readStringUntil('\n');
      i_s.trim();
      if (i_s.length() > 0) {
        flow = i_s.toFloat();
        set_speed();
      }
    }
    Serial.print("Speed: ");
    Serial.println(speed);
    Serial.print("Flow: ");
    Serial.println(flow);
    Serial.println("___________");
    last_time = time_now;
  }
}
