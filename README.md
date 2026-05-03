# Curtis' Drone Manager - A Block-Based Drone Control System

This project is a personal drone manager for both my DJI Tello and other lightweight DJI drones.
The application communicates wirelessly with the drone using UDP. Note that UDP does not **guarantee** that a packet will reach the drone, though the system has >95% transmission success rate.

This application is desgined for beginner/intermediate drone operators looking for intuitive 'scratch-like' software to program pre-set flight routines, particularly for filming and photography along a known flight plan.
The coloured blocks in the flight planner offer both drone command and program-logic functionality. This allows conditions to be evaluated at run-time when the drone is in-flight.

You will need an account to use this application, which may be registered and will be stored in the database. This is designed to run locally and mainly serves to allow users (me) to have different profiles for different uses.
For this reason do not store sensitive information in this application.
