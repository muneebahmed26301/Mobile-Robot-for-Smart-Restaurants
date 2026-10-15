#include <Arduino.h>
#include <micro_ros_arduino.h>
#include <stdio.h>
#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>
#include <std_msgs/msg/int32_multi_array.h>
#include <geometry_msgs/msg/twist.h>

// Motor 1 (RL) Config
#define en_motor_rl_a 26
#define en_motor_rl_b 25
#define pwmpin_rl_CW 14
#define pwmpin_rl_CCW 27

// Motor 2 (FR) Config
#define en_motor_fr_a 18
#define en_motor_fr_b 19
#define pwmpin_fr_CW 15
#define pwmpin_fr_CCW 2

// Motor 3 (RR) Config
#define en_motor_rr_a 4
#define en_motor_rr_b 16
#define pwmpin_rr_CW 5
#define pwmpin_rr_CCW 17

// Motor 4 (FL) Config
#define en_motor_fl_a 34
#define en_motor_fl_b 35
#define pwmpin_fl_CW 33
#define pwmpin_fl_CCW 32

// Channels
static const int pwm_chn_CW[] = {0, 2, 4, 6};
static const int pwm_chn_CCW[] = {1, 3, 5, 7};

// Vib Sensor Config
#define trig 12

// Motor Function Declarations
void motor_setup();
int GetEncoderTicks(int);
void enc_M1_Callback();
void enc_M2_Callback();
void enc_M3_Callback();
void enc_M4_Callback();

// Vib Function Declarations
void vib_setup();
int vib_read();

// ROSCommunication Class and Class Methods Declarations
class RosCommunication {
  public:
    RosCommunication();
    void setup();
    static void timer_callback(rcl_timer_t * timer, int64_t last_call_time);
    static void pwm_callback(const void *msg_in);
    void communicate();
};

int curr_enc_ticks[4] = { 0 };

void motor_setup(){
  for(int i = 0; i < 4; i++){
    ledcSetup(pwm_chn_CW[i] , 5000, 8);
    ledcSetup(pwm_chn_CCW[i], 5000, 8);
  }
    
  ledcAttachPin(pwmpin_fl_CW, pwm_chn_CW[0]);
  ledcAttachPin(pwmpin_fl_CCW, pwm_chn_CCW[0]);

  ledcAttachPin(pwmpin_rl_CW, pwm_chn_CW[1]);
  ledcAttachPin(pwmpin_rl_CCW, pwm_chn_CCW[1]);

  ledcAttachPin(pwmpin_fr_CW, pwm_chn_CW[2]);
  ledcAttachPin(pwmpin_fr_CCW, pwm_chn_CCW[2]);

  ledcAttachPin(pwmpin_rr_CW, pwm_chn_CW[3]);
  ledcAttachPin(pwmpin_rr_CCW, pwm_chn_CCW[3]);

  pinMode(en_motor_fl_a, INPUT_PULLDOWN);
  pinMode(en_motor_fl_b, INPUT_PULLDOWN);

  pinMode(en_motor_rl_a, INPUT_PULLDOWN);
  pinMode(en_motor_rl_b, INPUT_PULLDOWN);
  
  pinMode(en_motor_fr_a, INPUT_PULLDOWN);
  pinMode(en_motor_fr_b, INPUT_PULLDOWN);

  pinMode(en_motor_rr_a, INPUT_PULLDOWN);
  pinMode(en_motor_rr_b, INPUT_PULLDOWN);

  attachInterrupt(digitalPinToInterrupt(en_motor_fl_b), enc_M1_Callback, RISING);
  attachInterrupt(digitalPinToInterrupt(en_motor_rl_b), enc_M2_Callback, RISING);
  attachInterrupt(digitalPinToInterrupt(en_motor_fr_b), enc_M3_Callback, RISING);
  attachInterrupt(digitalPinToInterrupt(en_motor_rr_b), enc_M4_Callback, RISING);
}

void IRAM_ATTR enc_M1_Callback() {
  if (digitalRead(en_motor_fl_a) > 0) {
    curr_enc_ticks[0]++;
  } else {
    curr_enc_ticks[0]--;
  }
}

void IRAM_ATTR enc_M2_Callback() {
  if (digitalRead(en_motor_rl_a) > 0) {
    curr_enc_ticks[1]++;
  } else {
    curr_enc_ticks[1]--;
  }
}

void IRAM_ATTR enc_M3_Callback() {
  if (digitalRead(en_motor_fr_a) > 0) {
    curr_enc_ticks[2]++;
  } else {
    curr_enc_ticks[2]--;
  }
}

void IRAM_ATTR enc_M4_Callback() {
  if (digitalRead(en_motor_rr_a) > 0) {
    curr_enc_ticks[3]++;
  } else {
    curr_enc_ticks[3]--;
  }
}

void vib_setup() {
  pinMode(trig, INPUT);
}

int vib_read() {
  return digitalRead(trig);
}

rclc_executor_t executor;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;
rcl_subscription_t pwm_subscriber;
geometry_msgs__msg__Twist pwm_msg;
rcl_publisher_t enc_ticks_publisher;
rcl_timer_t timer;
std_msgs__msg__Int32MultiArray enc_ticks_msg;
#define RCCHECK(fn) { rcl_ret_t temp_rc = fn; if((temp_rc != RCL_RET_OK)){error_loop();}}
#define RCSOFTCHECK(fn) { rcl_ret_t temp_rc = fn; if((temp_rc != RCL_RET_OK)){}}

RosCommunication::RosCommunication() { }

void RosCommunication::setup(){
  Serial.begin(115200);
  set_microros_transports();

  delay(20);

  allocator = rcl_get_default_allocator();
  RCCHECK(rclc_support_init(&support, 0, NULL, &allocator));
  RCCHECK(rclc_node_init_default(&node, "micro_ros_esp32_node", "", &support));
  
  RCCHECK(rclc_subscription_init_default(&pwm_subscriber, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Twist), "/control/pwm"));
  RCCHECK(rclc_publisher_init_default(&enc_ticks_publisher, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32MultiArray),"/control/encoder_ticks"));
  RCCHECK(rclc_timer_init_default(&timer, &support, RCL_MS_TO_NS(50), timer_callback));
  
  unsigned int num_handles = 2; // subs + pubs
  RCCHECK(rclc_executor_init(&executor, &support.context, num_handles, &allocator));
  RCCHECK(rclc_executor_add_subscription(&executor, &pwm_subscriber, &pwm_msg, &RosCommunication::pwm_callback, ON_NEW_DATA));
  RCCHECK(rclc_executor_add_timer(&executor, &timer));
  
  Serial.println("micro_ros_esp32_node has been started");
}

void RosCommunication::timer_callback(rcl_timer_t * timer, int64_t last_call_time) {
  RCLC_UNUSED(last_call_time);
  if (timer != NULL) {
    int32_t enc_ticks_data[4];
    enc_ticks_msg.data.data = enc_ticks_data;
    enc_ticks_msg.data.size = 4;
    for (int i = 0; i < 4; i++) {
      enc_ticks_msg.data.data[i] = curr_enc_ticks[i];
    }
    RCSOFTCHECK(rcl_publish(&enc_ticks_publisher, &enc_ticks_msg, NULL));
  }
}

void RosCommunication::pwm_callback(const void *msg_in){
  const geometry_msgs__msg__Twist * pwm_msg = (const geometry_msgs__msg__Twist *)msg_in;
  int pwm[4] = {(int) pwm_msg->linear.x, (int) pwm_msg->linear.y, (int) pwm_msg->angular.x, (int) pwm_msg->angular.y};
  
  for (int i = 0; i < 4; i++) {
    if (pwm[i] > 0) {
      ledcWrite(pwm_chn_CCW[i], 0);
      ledcWrite(pwm_chn_CW[i], abs(pwm[i]));
    } else {
      ledcWrite(pwm_chn_CCW[i], abs(pwm[i]));
      ledcWrite(pwm_chn_CW[i], 0);
    }
  }
}

void RosCommunication::communicate(){
	RCSOFTCHECK(rclc_executor_spin_some(&executor, RCL_MS_TO_NS(100)));
  delay(10);
}

RosCommunication ros_communication;

void error_loop(){
  while(1);
}

void setup() {
  motor_setup();
  vib_setup();
  ros_communication.setup();
}

void loop() {
  ros_communication.communicate();
//  ledcWrite(pwm_chn_CCW[2], 0);
//  ledcWrite(pwm_chn_CW[2], 255);
//  ledcWrite(pwm_chn_CCW[2], 0);
//  ledcWrite(pwm_chn_CW[2], 255);
}
