# Created by Vladislav at 26.12.2015
Feature: client file list
  client can recieve file list with name and id

  Scenario: get file list
    client send query /files and get file list

Feature: demonize app
    application listen on port and waiting for connections

    Scenario: start application