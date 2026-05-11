Feature: configuration modification
  Module enables to create and update configuration

  Scenario: Update old configuration
  Given old configuration new configuration
  When update old configuration
  Then old configuration has been updated with new values


  Scenario: Set new value
  Given Configuration
  When Set new value
  Then New value has been set