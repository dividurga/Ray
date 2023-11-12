#include "VEML6070.h"
uint16_t uvs ;
//using Blynk server to host our interface
#define BLYNK_TEMPLATE_ID           "TMPL31C8e7R56"
#define BLYNK_TEMPLATE_NAME         "Quickstart Device"
#define BLYNK_AUTH_TOKEN            {AUTH_TOKEN}

#define BLYNK_PRINT Serial


#include <ESP8266WiFi.h>
#include <BlynkSimpleEsp8266.h>

// WiFi credentials.
char ssid[] = {SSID};
char pass[] = {PASSWORD};

BlynkTimer timer;

// This function is called every time the device is connected to the Blynk.Cloud
BLYNK_CONNECTED()
{
  // Change Web Link Button message to "Congratulations!"
  
}

//This function avoids spamming of data to the blynk cloud.
void myTimerEvent()
{
  // You can send any value at any time.
  // Please don't send more that 10 values per second.
  Blynk.virtualWrite(V2, millis() / 1000);
  //sends raw UV data to datastream V4
  Blynk.virtualWrite(V4, uvs);
}

void setup()
{
  // Debug console
  Serial.begin(9600);

  Blynk.begin(BLYNK_AUTH_TOKEN, ssid, pass);
  
  timer.setInterval(1000L, myTimerEvent);
  VEML.begin();
  //in IDE testing for sensor values
  Serial.println("Test sketch for VEML6070 UV sensor.");

}

void loop()
{
  //No blynk-specific data push/ pull requests to avoid spamming. 
  Blynk.run();
  timer.run();
  uvs = VEML.read_uvs_step();
  int risk_level = VEML.convert_to_risk_level(uvs);
  char* risk = VEML.convert_to_risk_char(risk_level);

  Serial.print("Current UVS is: ");
  Serial.print(uvs);
  Serial.print(", with current risk level: ");
  Serial.println(*risk);
  // delay of one second is low enough to not sever connection
    delay(1000);

  
}
