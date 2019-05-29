# ArduinoDQNCar

You will find here the code for a series of posts following up on running neural networks on an Arduino and pushing the concept furthermore by training first the neural network in a simulator then loading it to an Arduino and refining the training in vivo (my living room).

## How to use it

... to do ...

## Sources & Acknowledgments

This project relies on the following articles:

 * http://deeplizard.com/learn/video/nyjbcRQ-uQ8
 * https://github.com/keon/deep-q-learning
 * https://github.com/harvitronix/reinforcement-learning-car

And use:

 * https://github.com/viblo/pymunk
 * https://github.com/keras-rl/keras-rl
 * https://github.com/openai/gym
 * https://github.com/codeplea/genann

## Step 0: Ultrasonic Scanner

3D printed servo-mount for ultrasonic sensor and code to drive it.

## Step 1: Motor Speed PID Control

I tried to control motor speed using a PID control. However, the mechanic is too wobbly to produce any quality output.

## Step 2: Robot Simulator

Create a simulator where a simulated robot evolves

## Step 3: Deep Reinforcement Learning

Use the simulator and Keras-rl to train a neural network to drive the robot according to its environment.

## Step 4: Training Over BLE

Execute the training locally in the computer but run the environement on an arduino linked in BLE.

## Step 5: InVivo Reinforcement Learning

... to do ...

## Todo

### Cleanup

 - [x] Write the readme description and add github tags to the project
 - [x] Add references to used source code and licence repository
 - [x] Organize folders (Python, Dataset, Tinn, Articles Steps, Pictures, etc...)
 - [x] Split python simulator for DQN code (moved into Gym env)

### Get it working

 - [x] Fine tune hyper parameters
 - [x] Regularly save models
 - [ ] Implement training refinement in vivo
 - [ ] Write how to use it
 
### Improvements

 - [x] Improve simulator
 - [x] Improve DQN algo (moved to Keras-rl with crazy built-in rl algo)
 - [ ] Implement relu for Genann
