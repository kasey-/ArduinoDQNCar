from gym.envs.registration import register

register(
    id='arduino-v0',
    entry_point='gym_arduino.envs:ArduinoEnv',
)