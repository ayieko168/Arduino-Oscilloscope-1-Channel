
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


int vtrigger = 0; // The trigger voltage
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
unsigned long dtReal, tIni, tFim; // Variables for keeping the end time counter for flow state
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

  
  Serial.println("Initial boot of the board.");
  Serial.print("Version Number="); Serial.println(version_);
  //printHelp();
  //printConfig();  

  // Set the resistor and capacitor read pins
  pinMode(pinA, OUTPUT);
  pinMode(pinB, OUTPUT);
  RC_selector(0);
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
       lerResistorCapacitor();
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
       case 'h': // enviar help pela serial
          printHelp();
          break;
       case 'd': //alterar o valor de dt (us/ms)
          parsed_integer=Serial.parseInt(); // como e inteiro então vai de 0 a 32767 (parseint limita 16bits)
          if (parsed_integer>=1 && parsed_integer<=30000) {//28/08/15 deve ser dtmin=400us(3canais) dtmax=30000 
             dt=parsed_integer;
          } 
          first_read_char=Serial.read();
          if (first_read_char=='u' || first_read_char=='m'){
            unit_=first_read_char;
          } else { // sem unidade é segundo, então converter para mili (x1000)m
            unit_='m';
            dt*=1000;
          }
//          Serial.print("=> dt="); Serial.print(dt); Serial.print(unidade); Serial.println("s");
          break; 
       case 'q': // alterar valor do q.(ponto no final) (quantidade de leituras)
          parsed_integer=Serial.parseInt(); // inteiro de 0 a 32767
          first_read_char=Serial.read(); // para ir mais rápido colocar um . no final ex: q150.
          if (parsed_integer>=1 && parsed_integer<=qmax) {
             q=parsed_integer; 
          }
          //calcBuffer(); //não precisa pois será usado o qmax
          Serial.print("=> q="); Serial.println(q);
          break;
       case 'c': //cnm : n=0-3, m=(o)ativa/(x)desativa canal n exemplo:  c0x,  c2o
          delay(100);
          first_read_char=Serial.read();
          delay(100);
          second_read_char=Serial.read();
          if (first_read_char >= '0' && first_read_char <= '3'){
             if (second_read_char=='o'){
                channels_state[first_read_char-'0']=true;
             }else if (second_read_char=='x'){
                channels_state[first_read_char-'0']=false;
             }
             // recalcular o buffer para cada canal e colocar o indice
             // inicial para cada canal
             //Serial.println("entrar calcBuffer");
             calcBuffer();
             //Serial.println("saiu calcBuffer");
/*            Serial.print("=> Canais: ");
              for (k=0; k<3;k++){
                Serial.print("channels_state"); Serial.print(k); Serial.print("="); Serial.print(channels_state[k]);
              }
              Serial.println();
*/              
            }  
          break;
       case 't': // trigger: t(canal)
                 // trigger:  t0, t1, t2, t3
                 //           tx   desligado
                 //           tv512.  valor da tensão 0-1024 (5v)
        delay(100);
        first_read_char=Serial.read();
        if ((first_read_char>='0' && first_read_char<='3') || first_read_char=='x'){
           triggered_channel=first_read_char;      
        } else if (first_read_char=='v'){
          parsed_integer=Serial.parseInt();
          first_read_char=Serial.read();
          if (parsed_integer>=0 && parsed_integer<=1024) {
            vtrigger=parsed_integer;
          }
        }
        
//        Serial.print("=> triggered_channel="); Serial.println(triggered_channel);
        break;
       case '?':
          printConfig(); 
          break;
        case '1': // enviar Uma Amostra (q leituras)
          if (!once) once=true;
          if (once){
             various=false;
             flow=false; 
          }
//          Serial.print("=> once="); Serial.println(once);
          break;
        case 'v': // o(on)/x(off) - enviar Varias Amostras (q leituras cada)
           delay(100);
           first_read_char=Serial.read();
           if (first_read_char=='o') {
              various=true;
           } else {
              various=false;
           }
          if (various){
             once=false;
             flow=false; 
          }
//          Serial.print("=> various="); Serial.println(various);
          break;
        case 'f': // o(on)/x(off) - enviar Fluxo (ler e enviar - nao armazenar)
           delay(100);
           first_read_char=Serial.read();
           if (first_read_char=='o') {
              flow=true;
           } else {
              flow=false;
           }
          if (flow){
             various=false;
             once=false; 
             if (unit_=='u'){ // microsegundo
               tIni=micros(); tFim=tIni+dt;
             } else{ // milisegundo
               tIni=millis(); tFim=tIni+dt;
             }
          }
//          Serial.print("=> flow="); Serial.println(flow);
          break;
         case 'r': // (on/off) - enviar valor lido do Resistor em A5
           delay(100);
           first_read_char=Serial.read();
           if (first_read_char=='o') {
              read_RC=true;
           } else {
              read_RC=false;
           }
//           Serial.print("=> read_RC="); Serial.println(read_RC);
           dtRC=0;
           break;
         case 's': // Sinal: Ligar/desligar Gerador de Sinal
          delay(100);
          first_read_char=Serial.read();
          if (first_read_char=='o'){
            Timer1.restart(); // zera o contador
            Timer1.start(); //inicio
//            Serial.println("Timer1 restart/start");
          }else{
            Timer1.stop();
//            Serial.println("Timer1.stop()");
          }
          break;
         case 'p': // Sinal: alterar Período ex: p100m p343u
          parsed_float=Serial.parseFloat();
          if (parsed_float>0){
            first_read_char=Serial.read(); // ler unidade e converter para micro
//            Serial.print(">>parsed_float="); Serial.print(parsed_float); Serial.print(" c="); Serial.println(c);
            switch (first_read_char){
              case 'u': //já está em micro (u)
                pwmP=long(parsed_float);
                break;
              case 'm': // está em mili (m) então converter para micro (u)
                pwmP=long(parsed_float*1000.0);
//                Serial.print("parsed_float="); Serial.print(parsed_float); Serial.print("m"); Serial.print(" pwmP=parsed_float*1000="); Serial.println(pwmP);
                break;
              case ' ': // está em segundo ( ) então converter para micro (u)
                pwmP=long(parsed_float*1000000.0);
                break;
               default: // se veio caracter desconhecido faço o pwmP=1s
                pwmP=1000000l; // coloquei L no final do 100000 para dizer que é long
//                Serial.print("=> erro unidade pwmP, usando padrao(us)="); Serial.println(1000000);
                break;
            }
            Timer1.setPeriod(pwmP);
            Timer1.setPwmDuty(9,map(pwmPon,0,100,0,1023)); 
//            Serial.print("=> setPeriod="); Serial.println(pwmP);
          }
          break;
         case 'o': // Sinal: alterar tempo em ON ex: o25% o50%
          parsed_integer=int(Serial.parseFloat());
          first_read_char=Serial.read(); // só ler a % e desprezar (faz o parseInt ficar mais rapido
          if (parsed_integer>=0 && parsed_integer<=100){
            pwmPon=parsed_integer;
            Timer1.setPwmDuty(9,map(pwmPon,0,100,0,1023)); 
//            Serial.print("=> pwm on="); Serial.print(k); Serial.println("%");          
          }
          break;
         default:
           Serial.print("erro c="); Serial.println(first_read_char, HEX);
    }
  }
}

void calcBuffer(){
  //Serial.println("entrou calcBuffer");
  channels_on=0;
  // conta a quantidade de canais ativos
  for (int k=0;k<4;k++){
    if (channels_state[k]) {channels_on+=1;}
  }
  // calc size of each channel
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
  /*
  if (channels_on<=0) {
    qmax=0;
  } else {
    qmax=408/channels_on; // channels_on-qmax; 4-102; 3-136; 2-204; 1-408
  }
*/
  if (q>qmax) {
    q=qmax;
  }
  //Serial.print("q=408/channels_on=");Serial.print("408/");Serial.print(channels_on);Serial.print("=");Serial.println(q);
  // qtdCanais-qmax (channels_on-qmax) (4-100) (3-130) (2-200) (1-400)
  int chInit=0;
  for (int k=0; k<4; k++){
    if (channels_state[k]) {
      chs_init_pos_list[k]=chInit;
      chInit+=qmax;
    }
  }
  
 // Serial.print("channels_on="); Serial.print(channels_on); Serial.print(" q="); Serial.print(q); Serial.print(" qmax="); Serial.println(qmax);
//  for (int k=0; k<4; k++){
 //    Serial.print("k=");Serial.print(k); Serial.print(" chs_init_pos_list[k]="); Serial.println(chs_init_pos_list[k]);
 // }
  
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
   Serial.println("------ configuracoes -------");
   Serial.print(">? q="); Serial.println(q);
   Serial.print(">? qmax="); Serial.println(qmax);
   Serial.print(">? dt="); Serial.print(dt); Serial.print(unit_); Serial.println("s");
   float t=(float)q * (float)dt;
   Serial.print(" -> T=(q*dt)= "); Serial.print(t); Serial.print(unit_); Serial.println("s ");
   Serial.print(">? Canais: "); 
   for (int k=0; k<4; k++){
      Serial.print("  channels_state"); Serial.print(k); Serial.print("="); 
      if (channels_state[k]) {
        Serial.print("o");     
      } else {
        Serial.print("x");
      }
   }
   Serial.println();
   Serial.print(">? triggered_channel="); Serial.println(triggered_channel);
   Serial.print(">? once="); Serial.println(once);
   Serial.print(">? various="); Serial.println(various);
   Serial.print(">? flow="); Serial.println(flow);
   Serial.print(">? read_RC="); Serial.println(read_RC);
   Serial.print(">? pwmOn="); Serial.println(pwmOn);
   Serial.print(">? pwmP="); Serial.print(pwmP); Serial.println("us");
   Serial.print(">? pwmPon="); Serial.print(pwmPon); Serial.println("%");
}

unsigned long microsOuMillis(){
   if (unit_=='u'){
      return micros();
   } else {
      return millis();
   }
}

//-- procurar tensão maior que zero no triggered_channel ----
//-- se UMA=true então fica aguardando indefinitivamente
//-- se UMA=false então fica aguardando até o tempo tFIM (q*dt)
boolean trigger(){ // a variavel triggered_channel indica qual canal fará o trigger: 0,1,2 ou 3
  unsigned long tFim; // contador do tempo Final
  int v1=0,v2=0; 
  //int c1=0, c2=0;
  boolean achou=false;
    tFim=microsOuMillis()+q*dt;
    // dispara na subida do valor vtrigger+10
    //fica lendo a tensão enquanto for maior que vtrigger 
    //   E tempo menor que tFim
    do{
      v1=analogRead(triggered_channel-'0');
      //c1++;
    }while (v1>vtrigger && microsOuMillis()<tFim);
  //  while (v1=analogRead(triggered_channel-'0')>0 && microsOuMillis()<tFim){c1++;}
    if (v1<=vtrigger){
      tFim=microsOuMillis()+q*dt;
      //fica lendo a tensão enquanto for menor ou igual a 10+vtrigger
      // E tempo menor que tFim
      do{
        v2=analogRead(triggered_channel-'0');
        //c2++;
      }while(v2<=10+vtrigger && microsOuMillis()<tFim);
      //while (v2=analogRead(triggered_channel-'0')<=0 && microsOuMillis()<tFim){c2++;}
      if (v2>10+vtrigger){ 
        achou=true;
      }
      //Serial.print("v1="); Serial.print(v1); Serial.print(" v2=");Serial.println(v2);
      //Serial.print("c1=");Serial.print(c1);Serial.print(" c2=");Serial.println(c2);
    }
    return achou;
}

    
void sendVariousSamples(){

/*  
  // enviar quais canais serao enviados. ex: >ch=1<\t>3<\t>
  Serial.print(">channels_on="); Serial.print(channels_on); Serial.print("\t");
  for (int k=0; k<4; k++){
    if (channels_state[k]){Serial.print(k); Serial.print("\t");}    
  }
  Serial.println("");

  //enviar os valores dos canais
  for (int k=0; k<q; k++){
    Serial.print(">v="); Serial.print(k); Serial.print("\t");
    if (channels_state[0]) {Serial.print(chs_init_pos_list[0]+k); Serial.print("\t");}
    if (channels_state[1]) {Serial.print(chs_init_pos_list[1]+k); Serial.print("\t");}
    if (channels_state[2]) {Serial.print(chs_init_pos_list[2]+k); Serial.print("\t");}
    if (channels_state[3]) {Serial.print(chs_init_pos_list[3]+k); Serial.print("\t");}
    Serial.println("");
  }

  
  return;

  */

  
  unsigned long tFim; // contador do tempo Final
  unsigned long tTotalReal; // tempo Total da leitura dos valores.
    if (triggered_channel>='0' && triggered_channel<='3'){
      //Serial.print("triggered_channel=");Serial.println(triggered_channel);
      Serial.print("trigger="); Serial.println(trigger());
     }
    tTotalReal=microsOuMillis();

    for (int k=0; k<q; k++){
      tFim=microsOuMillis()+dt; 
/*
      if (channels_state[0]) {v0[k]=analogRead(A0);}
      if (channels_state[1]) {v1[k]=analogRead(A1);}
      if (channels_state[2]) {v2[k]=analogRead(A2);}
      if (channels_state[3]) {v3[k]=analogRead(A3);}
*/

      if (channels_state[0]) {values_buffer[chs_init_pos_list[0]+k] = analogRead(A0);}
      if (channels_state[1]) {values_buffer[chs_init_pos_list[1]+k] = analogRead(A1);}
      if (channels_state[2]) {values_buffer[chs_init_pos_list[2]+k] = analogRead(A2);}
      if (channels_state[3]) {values_buffer[chs_init_pos_list[3]+k] = analogRead(A3);}
      while (microsOuMillis()<tFim){}
    }

    
    tTotalReal=microsOuMillis()-tTotalReal; // total de tempo para ler todas as amostras
    dtReal=tTotalReal/q; // calcular o tempo médio de cada leitura
  Serial.println();
  Serial.print(">q="); Serial.println(q);
  Serial.print(">dt="); Serial.print(dt); Serial.print(unit_); Serial.println("s");
  Serial.print(">dtReal="); Serial.print(dtReal); //  Serial.print(unit_); Serial.println("s");
    if (unit_=='m'){
      Serial.println("e-3");
    }else if (unit_=='u'){
      Serial.println("e-6");
    }
    
  // enviar quais canais serao enviados. ex: >ch=1<\t>3<\t>
  Serial.print(">channels_on="); Serial.print(channels_on); Serial.print("\t");
  for (int k=0; k<4; k++){
    if (channels_state[k]){Serial.print(k); Serial.print("\t");}    
  }
  Serial.println("");
  
  //enviar os valores dos canais
  for (int k=0; k<q; k++){
    Serial.print(">v="); Serial.print(k); Serial.print("\t");
    if (channels_state[0]) {Serial.print(values_buffer[chs_init_pos_list[0]+k]); Serial.print("\t");}
    if (channels_state[1]) {Serial.print(values_buffer[chs_init_pos_list[1]+k]); Serial.print("\t");}
    if (channels_state[2]) {Serial.print(values_buffer[chs_init_pos_list[2]+k]); Serial.print("\t");}
    if (channels_state[3]) {Serial.print(values_buffer[chs_init_pos_list[3]+k]); Serial.print("\t");}
    Serial.println("");

  /* 
    if (channels_state[0]) {Serial.print(chs_init_pos_list[0]+k); Serial.print("\t");}
    if (channels_state[1]) {Serial.print(chs_init_pos_list[1]+k); Serial.print("\t");}
    if (channels_state[2]) {Serial.print(chs_init_pos_list[2]+k); Serial.print("\t");}
    if (channels_state[3]) {Serial.print(chs_init_pos_list[3]+k); Serial.print("\t");}
    Serial.println("");
  */
  }
 /* -- eliminado em 07/May/2017 - criei buffer dinamico  values_buffer[408] --   
  for (int k=0; k<q; k++){
    Serial.print(">v=");
    Serial.print(k); Serial.print("\t");
    Serial.print(v0[k]); Serial.print("\t");
    Serial.print(v1[k]); Serial.print("\t");
    Serial.print(v2[k]); Serial.print("\t");
    Serial.println(v3[k]);
  } 
  */ 
  Serial.print(">tTotalReal="); Serial.print(tTotalReal); //Serial.print(unit_); Serial.println("s");
    if (unit_=='m'){
      Serial.println("e-3");
    }else if (unit_=='u'){
      Serial.println("e-6");
    }
}

void sendFlowSamples(){
  int v0, v1, v2, v3; // guarda os valores das leituras
  //byte v0, v1, v2, v3; // guarda os valores das leituras
  boolean leu=false;
    if (microsOuMillis()>=tFim){
      dtReal=microsOuMillis()-tIni;
      tIni=microsOuMillis(); tFim=tIni+dt;
      if (channels_state[0]) {v0=analogRead(A0);}
      if (channels_state[1]) {v1=analogRead(A1);}
      if (channels_state[2]) {v2=analogRead(A2);}
      if (channels_state[3]) {v3=analogRead(A3);}
      //if (channels_state[0]) {v0=analogRead(A0)/4;}
      //if (channels_state[1]) {v1=analogRead(A1)/4;}
      //if (channels_state[2]) {v2=analogRead(A2)/4;}
      //if (channels_state[3]) {v3=analogRead(A3)/4;}
      leu=true;
    }
  if (leu){
    Serial.print(">f=");
    Serial.print("0"); Serial.print("\t");
    Serial.print(dtReal); 
      if (unit_=='m'){
        Serial.print("e-3");
      }else if (unit_=='u'){
        Serial.print("e-6");
      }
      Serial.print("\t");
    if (channels_state[0]) {Serial.print(v0);} else {Serial.print("0");} Serial.print("\t");
    if (channels_state[1]) {Serial.print(v1);} else {Serial.print("0");} Serial.print("\t");
    if (channels_state[2]) {Serial.print(v2);} else {Serial.print("0");} Serial.print("\t");
    if (channels_state[3]) {Serial.println(v3);} else {Serial.println("0");}
  }
}

//=========== Rotinas para leitura de Resistor e Capacitor ===========

void lerResistorCapacitor(){
  descarregar();
  lerEntrada(1);
  if (vf-vi>=100) {// e' capacitor
    calcCapacitor();
  } else {
    if (v<900) { // calcular valor do resistor
      calcRx();
    } else { // subir selecionar 2
      // descarregar se for capacitor
      descarregar();
      lerEntrada(2);
      if (vf-vi>=100) { // capacitor - escala 2
        calcCapacitor();
      } else { // resistor
        if (v<900){ // calcular valor do resistor
          calcRx();
        } else { // subir selecionar 3 (nao consegue detectar capacitor corretamente)
          lerEntrada(3);
          if (v<900){
            calcRx();
          } else {
            Serial.println(">rc=3\tColoque RC");
          }
        }
      }
    }
  }
}

void calcCapacitor(){
  float re[]={0.0,145.2,20692.9,1017847.5};
  float cx=0;
  descarregar();
  RC_selector(1);
  dtRC=millis(); 
  while (analogRead(pinV)<647){} // 647 = 63.2% Vcc => (nessa voltagem  t=rc)
  dtRC=millis()-dtRC; 
  if (dtRC>=100) { // dentro da faixa Cx>1mF
    cx=(float)dtRC/re[entrada];
    unidadeRC='m';  //resultado em mF
  } else { // fora da faixa, subir para escala 2
    descarregar();
    RC_selector(2);
    dtRC=millis();
    while (analogRead(pinV)<647){}
    dtRC=millis()-dtRC;
    if (dtRC>=10) { // dentro da faixa 
      cx=(float)dtRC*1000.0/re[entrada];
      unidadeRC='u'; // resultado em uF
    } else { // fora da faixa, então subir escala
      descarregar();
      RC_selector(3);
      dtRC=millis();
      while (analogRead(pinV)<647){}
      dtRC=millis()-dtRC;
      cx=(float)dtRC*1000000.0/re[entrada]; 
      unidadeRC='n'; // resultado em nF
    }
  }
  Serial.print(">c="); Serial.print(entrada); Serial.print("\t"); Serial.print(cx); Serial.print(" "); Serial.print(unidadeRC); Serial.println("F");
}

void lerEntrada(byte e){
  RC_selector(e);
  dtRC=micros();
  vi=analogRead(pinV);
  v=0;
  for (int k=0; k<10; k++){
     v+=analogRead(pinV);
  }
  v/=10;
  vf=analogRead(pinV);
  dtRC=micros()-dtRC;
}

void descarregar(){
  RC_selector(0);
  while (analogRead(pinV)>0){}
}

void calcRx(){
  float re[]={0.0,145.2,20692.9,1017847.5};
  float vcc[]={0,871.5,1026.3,1027.1};
  float rx=0;
  rx=re[entrada]*(float)v/(vcc[entrada]-(float)v);
  Serial.print(">r="); Serial.print(entrada); Serial.print("\t");
  switch (entrada) {
     case 1:
      if (rx>=1000){
        rx/=1000;
        Serial.print(rx); Serial.println(" Kohm");
      } else {
        Serial.print(rx); Serial.println(" ohm");
      }
      break;
     case 2:
      Serial.print(rx/1000); Serial.println(" Kohm");
      break;
     case 3:
      Serial.print(rx/1000000); Serial.println(" Mohm");
      break; 
  }
}

void RC_selector(byte e){
  entrada=e;
  digitalWrite(pinA,bitRead(entrada,0));
  digitalWrite(pinB,bitRead(entrada,1));
}
