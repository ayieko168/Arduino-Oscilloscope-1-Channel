
#define version_ "v1.5"

/* 
 *  working with TimerOne
  Timer1.initializa(us);  // initializes timer1(call first)
  Timer1.setPeriodo(us); // new period
  Timer1.start(); // 
  Timer1.stop();
  Timer1.restart();
  Timer1.resume();
  Timer1.pwm(pin,duty); pin 9 ou 10, dute(0-1023) (use first in pwm)
  Timer1.setPwmDuty(pin,duty); //reconfigure pwm
  Timer1.disablePwm(pin); //stop using pwm on a pin. (back to digitalWrite())
  Timer1.attachInterrupt(function);// run the function as an interrupt so use "volatile" in the name of variables 
  Timer1.detachInterrupt();//
  noInterrupts();
   blinkCopy=blinkCount; // turn off the interruption to pass the volatile variable
  interrupts();
  
*/


#include <TimerOne.h>

//--- constant for prescaler configuration ======
// I will use PS_16
const unsigned char PS_16 = (1 << ADPS2);
const unsigned char PS_32 = (1 << ADPS2) | (1 << ADPS0);
const unsigned char PS_64 = (1 << ADPS2) | (1 << ADPS1);
const unsigned char PS_128 = (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0);
// configure in the setup: ADC
//======================================

boolean  pwmOn=true; 
unsigned long pwmP=20000; //Period 20000us=20ms=0.02s => 50Hz
byte pwmPon=25; // % of pwmP in HIGH


// Samples And Channels configurations
//======================================
int values_buffer[400]; // (100*4=400) : A buffer stores the measure values (analogRead() Values) of all channels
int chs_init_pos_list[] = {0,100,200,300}; // A list containing each channel's init position on the buffer (values_buffer[])
int channels_on = 4; // The number of channels are currently ON
int q = 100; // The number of readings for each channel
int qmax = 100; // The maximum quantity allowed for q ; channels_on-qmax; 4-100; 3-130; 2-200; 1-400


int trigger_voltage = 0; // The trigger voltage
boolean channels_state[] = {true,true,true,true}; // A list containing the channel states. (Modify to enable/disable channels) (True=enable, False=Disable)
unsigned int dt = 4; // 100us to 1000us(1ms) to 3000ms(3s) - Controlls time between each sample - Samlpling Period
char unit_ = 'm'; // unit : m = millisecond, u = microsecond

// note: for reading the 3 channels the minimum time is approximately 380us
// note: for reading the 4 channels the minimum time is approximately 500us
//   Therefore:   1 channel should give 120us


// Sampling Configurations
boolean various = false; // v = several
boolean once = false;    // u = onece
boolean flow = false; // f = data flow (sends each reading without saving it in memory) : speed limited by the 115200 serial
unsigned long dtReal, tIni, final_counter_time; // Variables for keeping the end time counter for flow state
char triggered_channel = 'x'; // Variable that sets what channel is triggered : '0', '1', '2', '3' (trigger channel), 'x' = no trigger


//--------------- Read Resistor / Capacitor Configurations ---------
boolean read_RC = false; // Boolean for weather to read the resistor/capacitor value
#define pinV 5
#define pinA 7 // pin A 10 multiplex
#define pinB 8 // pin B 9 multiplex
byte entrada = 0;
int vi, vf, v;
//float rx=0, cx=0;
//float r[]={0.0,200.0,20000.0,1000000.0};
//float re[]={0.0,145.2,20692.9,1017847.5};
//float vcc[]={0,871.5,1026.3,1027.1};
unsigned long dtRC=0;
char unidadeRC=' ';
boolean debug=true;
//-------------------------------------------------------------------

void setup() {


 //---------- Configure the ADC preescaler -------------------
 ADCSRA &= ~PS_128; // Clears arduino library configuration
 
  // Possible prescaler values. Just uncomment the line with desired prescaler
  // PS_16, PS_32, PS_64 or PS_128
  //ADCSRA |= PS_128; // 64 prescaler
  //ADCSRA |= PS_64; // 64 prescaler
  //ADCSRA |= PS_32; // 32 prescaler
  ADCSRA |= PS_16; // 16 prescaler
  //----------------------------------------------------------
  
  //Set Timer1 pwm (pin9) and pin10 to monitor frequency
  pinMode(10, OUTPUT);
  Timer1.initialize(pwmP); // I will start with a Period of 20000us=20ms=0.02s => 50Hz
  Timer1.pwm(9, map(pwmPon, 0, 100, 0, 1023)); // pwm on pin9 with 25% duty cycle
  Timer1.attachInterrupt(callback); // attaches callback() as timer overflow interrupt
  //Timer1.stop();


  // Uncomment the desired daud rate (default=115200)
  //Serial.begin(9600);
  Serial.begin(115200);
  //Serial.begin(250000);
  Serial.println();

  
//  Serial.println("Initial /boot of the board.");
  Serial.print("Version Number="); Serial.println(version_);
  //printHelp();
  //printConfig();  

  // Set the resistor and capacitor read pins
  pinMode(pinA, OUTPUT);
  pinMode(pinB, OUTPUT);
}

void callback(){
  digitalWrite(10, digitalRead(10)^1); // ^1 = xor (0->1, 1->0)
}

void loop() {
   readSerial();
   if (various) {
      sendVariousSamples();
   } 
   
   else if (once) {
      if (triggered_channel == 'x'){
        sendVariousSamples();
        once=false;
      }
      else {
        if (trigger()){
          sendVariousSamples();
          once=false;
        }
      }
   }
   
   else if (flow) {
      sendFlowSamples(); 
   }
   
   if (read_RC){
     if (millis()>=dtRC){
       readResistorCapasitor();
       dtRC=millis()+3000;
     }
   }
}

void readSerial(){
  
  int parsed_integer;
  float parsed_float;
  char first_read_char, second_read_char;
  
  if (Serial.available() > 0){
    first_read_char = Serial.read();
    
    switch (first_read_char){
       case 'h': // Send help via serial
          printHelp();
          break;
       
       case 'd': // change the value of dt;(Sampling Period) - Syntax: d(integer)(unit) - Example: d652u, d859m, d565=d565s=d565S
          parsed_integer=Serial.parseInt(); // Accepts an integer then goes from 0 to 32767 (parseint limits 16bits) and must be dtmin = 400us (3channels) dtmax = 30000
          if (parsed_integer >= 1 && parsed_integer <= 30000) {
             dt = parsed_integer;
          } 
          
          first_read_char=Serial.read(); // Parse for the sent unit of measurement
          if (first_read_char=='u' || first_read_char=='m'){
            unit_ = first_read_char;
          } 
          else { // Without unit is second, then convert to milli (x1000) m
            unit_ = 'm';
            dt*=1000;
          }

          break; 
       
       case 'q': // change q value (number of readings on the buffer)
          parsed_integer=Serial.parseInt(); // Integer from 0 to 32767
          first_read_char=Serial.read(); // To parse faster put one. at the end eg: q150.
          
          if (parsed_integer>=1 && parsed_integer<=qmax) {
             q=parsed_integer; 
          }
          //calcBuffer(); // you don't need it because qmax will be used
          Serial.print("=> q="); Serial.println(q);
          break;
       
       case 'c': // Disable or Enable a channel - Syntax: c(channel)(mode): channel = 0-3, mode = (o)enables & (x)disables channel n - Example: c0x, c2o
          delay(100);
          first_read_char=Serial.read();
          delay(100);
          second_read_char=Serial.read();
          
          if (first_read_char >= '0' && first_read_char <= '3'){
             if (second_read_char=='o'){
                channels_state[first_read_char-'0'] = true;
             }
             else if (second_read_char=='x'){
                channels_state[first_read_char-'0'] = false;
             }
             // Recalculate the buffer size for each channel and update the initial index for each channel on the values buffer
             calcBuffer();
            }  
          break;
       
       case 't': // Set the triggered channel or the trigger volteage(value 0-1024 (5v)) - Syntax: t(channel) or tv(voltage) or tx=trigger off - Examples: t0, t1, t2, t3, tv512
        delay(100);
        first_read_char=Serial.read();
        
        if ((first_read_char >= '0' && first_read_char <= '3') || first_read_char == 'x'){
           triggered_channel = first_read_char;      
        }
        else if (first_read_char=='v'){
          parsed_integer=Serial.parseInt();
          first_read_char=Serial.read();
          
          if (parsed_integer >= 0 && parsed_integer <= 1024) {
            trigger_voltage = parsed_integer;
          }
        }
          break;
       
       case '?':
          printConfig(); 
          break;
       
       case '1': // Send A Sample (q readings)
          if (!once) once=true;
          
          if (once){
             various=false;
             flow=false; 
          }

          break;
       case 'v': // Send Multiple Samples (of q readings each) - Syntax: v(o|x)>o(on)/x(off)
           delay(100);
           first_read_char = Serial.read();
           
           if (first_read_char == 'o') {
              various=true;
           }
           else {
              various=false;
           }
          
          if (various){
             once=false;
             flow=false; 
          }
          
          break;
       case 'f': // Send A flow of raw readings, do not store on buffer - Syntax: f(o|x)>o(on)/x(off)
           delay(100);
           first_read_char=Serial.read();
           
           if (first_read_char == 'o') {
              flow = true;
           }
           else {
              flow = false;
           }
           
           if (flow){
             various=false;
             once=false; 
             
             if (unit_=='u'){ // microsecond
               tIni = micros(); 
               final_counter_time = tIni + dt;
             }
             else{ // millisecond
               tIni = millis(); 
               final_counter_time = tIni + dt;
             }
          }

          break;
       
       case 'r': // Send value read from Resistor in pin A5 - Syntax: r(o|x)>o(on)/x(off)
           delay(100); 
           first_read_char = Serial.read();
           
           if (first_read_char == 'o') {
              read_RC=true;
           } 
           else {
              read_RC=false;
           }
           dtRC=0;
           break;
       case 's': // Signal Generator: Turn Signal Generator on / off - Syntax: s(o|x)>o(on)/x(off)
          delay(100);
          first_read_char = Serial.read();
          
          if (first_read_char=='o'){
            Timer1.restart(); // Reset the counter
            Timer1.start(); // start
          }
          else{
            Timer1.stop(); // Stop the counter
          }
          break;
       case 'p': // Signal Generator: Change the signal generator's period - Syntax: p(period_float)(unit)> - Example: p100m p343u
          parsed_float = Serial.parseFloat();
          
          if (parsed_float > 0){
            first_read_char = Serial.read();
            
            switch (first_read_char){
              case 'u': // if paresd unit is already in micro(u)
                pwmP = long(parsed_float);
                break;
              case 'm': // if parsed unit is in milli(m), then convert to micro(u)
                pwmP=long(parsed_float * 1000.0);
                break;
              case ' ': // if the parsed unit is in second(), then convert to micro(u)
                pwmP=long(parsed_float*1000000.0);
                break;
               default: // if an unknown character is parsed, set pwmP = 1second
                pwmP=1000000l; // I put L at the end of 100000 to say it’s long
                break;
            }
            Timer1.setPeriod(pwmP);
            Timer1.setPwmDuty(9, map(pwmPon, 0, 100, 0, 1023)); 
          }
          break;
       case 'o': // Signal Generator: change the PWM signal's time on ON - Syntax: o(time<100)% - Example: o25% o50%
          parsed_integer = int(Serial.parseFloat());
          first_read_char = Serial.read(); // just read the % and pass it to make the parseInt faster
          
          if (parsed_integer >= 0 && parsed_integer <= 100){
            pwmPon = parsed_integer;
            Timer1.setPwmDuty(9, map(pwmPon, 0, 100, 0, 1023)); 
          }
          break;
       
       default:
           Serial.print("erro c= "); Serial.println(first_read_char, HEX);
    }
  }
}

void calcBuffer(){
  // Reset the channels on variable and Recount the number of active channels.
  channels_on = 0;
  for (int k=0; k<4; k++){
    if (channels_state[k]) {channels_on+=1;}
  }
  
  // Calculate the size of each channel
  switch (channels_on){
    case 0:
      qmax=0;
      break;
    case 1:
      qmax=400;
      break;
    case 2:
      qmax=200;
      break;
    case 3:
      qmax=130;
      break;
    case 4:
      qmax=100;
      break;
  }

  if (q > qmax) {
    q = qmax;
  }
  
  // Recalculate the initial position of the active channel's data in the data buffer
  int chInit=0;
  for (int k=0; k<4; k++){
    if (channels_state[k]) {
      chs_init_pos_list[k] = chInit;
      chInit+=qmax;
    }
  }
}

void printHelp(){
   Serial.println("-----------------------");
   Serial.print("! BegOscopio "); Serial.print(version_); Serial.println(" - rogerio.bego@hotmail.com !");
   Serial.println("-----------------------");
/*
   Serial.println("----------- help ---------------------");
   Serial.println(" h    : help");
   Serial.println(" ?    : exibir as configuracoes atuais");
   Serial.println(" -------- controle da amostragem ------");
   Serial.println(" d___ : d[1-3000][un] - ex: d100m, d200u - dt = intervalo de tempo (us/ms) entre as leituras");
   Serial.println(" q___ : q[1-100]. - qtd de leituras");
   Serial.println(" cn_  : (o)ativa,(x)desativa canal: ex:  c2o (ativar channels_state2), c0x (desativar channels_state0)");
   Serial.println(" t_   : 0,1,2,3(canal),x(off)  ");
   Serial.println(" tv__ : tv512.  valor da tensao 0-1024 (0-5v)");
   Serial.println(" -------- envio das amostras ---------");
   Serial.println(" 1    : enviar once amostra");
   Serial.println(" v_   : o(on),x(off) enviar various amostras");
   Serial.println(" f_   : o(on),x(off) enviar flow de dados");
   Serial.println("    obs:  1, v, f sao mutuamente excludentes");
   Serial.println(" -------- leitura de Resistor ou Capacitor ----");
   Serial.println(" r_   : o(on),x(off) ler Resistor ou Capacitor");
   Serial.println(" -------- Gerador de Sinal pwm ---------");
   Serial.println(" s_   : o(on),x(off) ativa Ger.Sinal (pwm na porta 9) (porta 10 indica 2*T)");
   Serial.println(" p_   : p[valor][unidade] periodo do sinal de 100u a 8s");
   Serial.println(" o_   : o[0-100][%] Ton em porcentagem");
   Serial.println("----------------------------------------");
   */
}

void printConfig(){
   Serial.println(">>>Configurations...");
   Serial.print(">? q="); Serial.println(q);
   Serial.print(">? qmax="); Serial.println(qmax);
   Serial.print(">? dt="); Serial.print(dt); Serial.print(unit_); Serial.println("s");
   float t = (float)q * (float)dt;
   Serial.print(">? T=(q*dt)= "); Serial.print(t); Serial.print(unit_); Serial.println("s ");
   Serial.print(">? Channels: "); 
   for (int k=0; k<4; k++){
      Serial.print("Channel-"); Serial.print(k+1); Serial.print(" is "); 
      if (channels_state[k]) {
        Serial.print("ON, ");     
      } else {
        Serial.print("OFF, ");
      }
   }
   Serial.println();
   Serial.print(">? Triggered Channel="); Serial.println(triggered_channel);
   Serial.print(">? once="); Serial.println(once);
   Serial.print(">? various="); Serial.println(various);
   Serial.print(">? flow="); Serial.println(flow);
   Serial.print(">? read_RC="); Serial.println(read_RC);
   Serial.print(">? pwmOn="); Serial.println(pwmOn);
   Serial.print(">? pwmP="); Serial.print(pwmP); Serial.println("us");
   Serial.print(">? pwmPon="); Serial.print(pwmPon); Serial.println("%");
}

unsigned long microsOrMillis(){
   if (unit_=='u'){
      return micros();
   } 
   else {
      return millis();
   }
}

boolean trigger(){
  //-- look for voltage greater than zero in triggered_channel ----
  //-- if once = true then it waits indefinitely
  //-- if once = false then wait until time final_counter_time (q * dt)
  //-- the triggered_channel variable indicates which channel will trigger: 0, 1, 2 or 3
  
  unsigned long final_counter_time; // Final time of the counter
  int v1=0, v2=0; 
  boolean found=false;
  final_counter_time = microsOrMillis() + q * dt;
  
  /* Triggers on the rising edge of the reading, because of <trigger_voltage+10>, as long as the reading 
  is greater than <trigger_voltage> And time less than final_counter_time, You can set the trigger to a 
  falling edge by changing <trigger_voltage+10> to <trigger_voltage-10>
  */
  do{
    v1 = analogRead(triggered_channel-'0');
  }
  while (v1 > trigger_voltage && microsOrMillis() < final_counter_time);
  if (v1 <= trigger_voltage){
    final_counter_time = microsOrMillis() + q * dt;
    do{
      v2 = analogRead(triggered_channel-'0');
    }
    while(v2 <= 10+trigger_voltage && microsOrMillis()<final_counter_time);
    if (v2 > 10+trigger_voltage){ 
      found=true;
    }
  }
  return found;
}
 
void sendVariousSamples(){
  
  unsigned long final_counter_time; // Final time counter
  unsigned long tTotalReal; // Total time of reading the values.
  
  if (triggered_channel >= '0' && triggered_channel <= '3'){
    Serial.print("trigger="); Serial.println(trigger());
   }
  tTotalReal = microsOrMillis();

  for (int k=0; k<q; k++){
    final_counter_time = microsOrMillis()+dt; 

    // if a channel is activated, at its initial buffer position, append q reading to the buffer
    if (channels_state[0]) {values_buffer[chs_init_pos_list[0]+k] = analogRead(A0);}
    if (channels_state[1]) {values_buffer[chs_init_pos_list[1]+k] = analogRead(A1);}
    if (channels_state[2]) {values_buffer[chs_init_pos_list[2]+k] = analogRead(A2);}
    if (channels_state[3]) {values_buffer[chs_init_pos_list[3]+k] = analogRead(A3);}
    while (microsOrMillis() < final_counter_time){}
  }

  tTotalReal = microsOrMillis() - tTotalReal; // total time to read all samples
  dtReal = tTotalReal / q; // calculate the average time of each reading
  
  Serial.println();
  Serial.print(">q="); Serial.println(q);
  Serial.print(">dt="); Serial.print(dt); Serial.print(unit_); Serial.println("s");
  Serial.print(">dtReal="); Serial.print(dtReal); //  Serial.print(unit_); Serial.println("s");
  if (unit_=='m'){
    Serial.println("e-3");
  }else if (unit_=='u'){
    Serial.println("e-6");
  }
    
  //Send which channels will be sent. Example:> channels_on = 1 3 - TAb delemeted
  Serial.print(">channels_on="); Serial.print(channels_on); Serial.print("\t");
  for (int k=0; k<4; k++){
    if (channels_state[k]){Serial.print(k); Serial.print("\t");}    
  }
  Serial.println("");
  
  //Send the channel values from the buffer - Tab delemeted
  for (int k=0; k<q; k++){
    Serial.print(">v="); Serial.print(k); Serial.print("\t");
    if (channels_state[0]) {Serial.print(values_buffer[chs_init_pos_list[0]+k]); Serial.print("\t");}
    if (channels_state[1]) {Serial.print(values_buffer[chs_init_pos_list[1]+k]); Serial.print("\t");}
    if (channels_state[2]) {Serial.print(values_buffer[chs_init_pos_list[2]+k]); Serial.print("\t");}
    if (channels_state[3]) {Serial.print(values_buffer[chs_init_pos_list[3]+k]); Serial.print("\t");}
    Serial.println("");
  }
 
  Serial.print(">tTotalReal="); Serial.print(tTotalReal);
  if (unit_=='m'){Serial.println("e-3");} else if (unit_=='u'){Serial.println("e-6");}
}

void sendFlowSamples(){
  int v0, v1, v2, v3; // Variables that stores readings values
//  byte v0, v1, v2, v3; // Variables that stores readings values, uses less flash storage
  boolean done_reading = false;
  
  if (microsOrMillis() >= final_counter_time){
    dtReal=microsOrMillis() - tIni;
    tIni=microsOrMillis();
    final_counter_time = tIni + dt;
    
    if (channels_state[0]) {v0=analogRead(A0);}
    if (channels_state[1]) {v1=analogRead(A1);}
    if (channels_state[2]) {v2=analogRead(A2);}
    if (channels_state[3]) {v3=analogRead(A3);}
    done_reading=true;
  }
  
  if (done_reading){
    Serial.print(">f=");
    Serial.print("0"); Serial.print("\t");
    Serial.print(dtReal); 
    if (unit_=='m'){Serial.print("e-3");}else if (unit_=='u'){Serial.print("e-6");}
    Serial.print("\t");
    // If the channel is activated, print the read value to serial. - Tab delemeted
    if (channels_state[0]) {Serial.print(v0);} else {Serial.print("0");} Serial.print("\t");
    if (channels_state[1]) {Serial.print(v1);} else {Serial.print("0");} Serial.print("\t");
    if (channels_state[2]) {Serial.print(v2);} else {Serial.print("0");} Serial.print("\t");
    if (channels_state[3]) {Serial.println(v3);} else {Serial.println("0");}
  }
}

//=========== Routines for Reading Resistor and Capacitor ===========

void readResistorCapasitor(){
  byte val;
  }
