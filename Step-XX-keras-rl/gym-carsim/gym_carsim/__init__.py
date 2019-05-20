from gym.envs.registration import register

register(
    id='carsim-v0',
    entry_point='carsim_foo.envs:CarSimEnv',
)