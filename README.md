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
 * https://github.com/codeplea/genann

## Step 0: Ultrasonic Scanner

## Step 1: Motor Speed PID Control

## Step 2: Robot Simulator

## Step 3: Deep Reinforcement Learning

## Step 4: Robot Bluetooth Update

## Step 5: InVivo Reinforcement Learning

## Todo

### Cleanup

 - [x] Write the readme description and add github tags to the project
 - [x] Add references to used source code and licence repository
 - [x] Organize folders (Python, Dataset, Tinn, Articles Steps, Pictures, etc...)
 - [x] Split python simulator for DQN code (moved into Gym env)

### Get it working

 - [x] Fine tune hyper parameters
 - [x] Regularly save models
 - [ ] Refactor code to generate training dataset for Gennan
 - [ ] Implement training refinement in vivo
 - [ ] Write how to use it
 
### Improvements

 - [ ] Improve simulator
 - [x] Improve DQN algo (moved to Keras-rl with crazy built-in rl algo)
 - [ ] Implement relu for Genann
