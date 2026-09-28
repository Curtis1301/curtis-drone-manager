# Curtis' Drone Manager - A Block-Based Drone Control System

*Originally developed throughout 2025, this repository exists as a portfolio of the project*

This PyQt application is a block-based flight control system for the DJI Tello mini-drone. This project is intended for personal use, though may be used with other drones that make use of the *Ryze Tello SDK*. Drone commands can be set within the  application, which communicates wirelessly with the drone using UDP. UDP does not guarantee that a packet will reach the drone, though the system has >95% transmission success rate.

## Overview

This application is desgined for beginner/intermediate drone operators looking for intuitive 'scratch-like' software to program pre-set flight routines, particularly for filming and photography along a known flight plan. The coloured blocks in the flight planner offer both drone command and program-logic functionality. This allows conditions to be evaluated at run-time when the drone is in-flight.

You will need an account to use this application, which may be registered and will be stored in the database. This is designed to run locally and primarily enables users to have different profiles for different uses. For this reason do not store sensitive information in this application.

## Features

+ Pre-planned and real-time control over the DJI Tello using UDP
+ Flight control GUI built using PyQt
+ Block-based, drag-and-drop flight plan construction interface
+ Logic control commands to enable logic within flight plans
+ SQLite database for storing persistent data (including accounts and drone data)
+ Ability to customise UDP commands according to the Tello SDK - or otherwise speciifc drone instruction set
+ Real-time drone camera video feed display

## Architecture

The application is divided into eight main components:

+ Blocks and Workspace layer defines the drag-and-drop system and specifies how blocks behave and are displayed. 
+ Drone control layer controls communication with the drone, including sending and receiving commands over UDP
+ Flight control layer handles manual flight mode, in which commands are sent to the drone as they are given by the user
+ Image processing layer that converts image frames received in real-time into displayable images
+ Telemetry layer that handles the requesting and processing of the drone's real-time telemetry data
+ Summary/Control layer that enables customization of the UDP commands that get sent to the drone
+ Database layer that handles data persistence
+ PyQt GUI which controls the layout and structure of the overall GUI

## Technologies

| Area | Technology |
|------|------------|
| Language | Python |
| GUI | PyQt |
| Networking | UDP & Sockets |
| Database | SQLite |
| Hardware | DJI Ryze Tello |
| Version Control | Git |

## How it works

### General

1. The user either logs into an existing account or creates a new one
2. The user selects an existing or adds a new drone (in which case the drone's command set must be specified)
3. Communication with the drone can be started or ended at any time

### Command Block Mode

This is the application's default mode. The application will not be able to send any commands until a valid sequnce has been set

1. XXX

### Manual Control Mode


## Getting started

## Example / Demo

## Testing

## Design decisions

## Limitations and future improvements