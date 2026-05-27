import gymnasium as gym
import numpy as np
import cv2


class GymWrapper(gym.Wrapper):
    def __init__(self, env):
        super().__init__(env)

        self.action_space = env.action_space

        self.obs_size = (96, 96)
        self.action_repeat = 1
        self.hybrid_obs = False
        self.grayscale = True

        self.max_x = 0
        self.last_x = 0
        self.stale_steps = 0
        self.min_progress_delta = 8
        self.stale_limit = 600

        channels = 1 if self.grayscale else 3
        self.observation_space = gym.spaces.Box(
            low=0,
            high=255,
            shape=(channels, self.obs_size[0], self.obs_size[1]),
            dtype=np.uint8,
        )

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        # noinspection PyUnresolvedReferences
        x_pos = self._player_x(self.env.unwrapped.get_ram())

        self.max_x = x_pos
        self.last_x = x_pos
        self.stale_steps = 0

        return self._process_observation(obs), info

    def step(self, action):
        obs = None
        terminated = False
        truncated = False
        info = {}

        for _ in range(self.action_repeat):
            obs, _, terminated, truncated, info = self.env.step(action)
            if terminated or truncated:
                break

        info = info or {}
        # noinspection PyUnresolvedReferences
        ram = self.env.unwrapped.get_ram()

        x_pos = self._player_x(ram)
        progress_delta = max(0, x_pos - self.max_x)
        reward = float(progress_delta)

        if progress_delta >= self.min_progress_delta:
            self.max_x = x_pos
            self.stale_steps = 0
        else:
            self.stale_steps += 1

        dead = self._is_dead(ram)
        won = self._is_won(ram)
        stale = self.stale_steps > self.stale_limit

        if dead or won:
            terminated = True
        if stale:
            truncated = True

        info.update(
            {
                "won": won,
                "dead": dead,
                "stale": stale,
                "progress": self.max_x,
            }
        )

        self.last_x = x_pos
        return self._process_observation(obs), reward, terminated, truncated, info

    def _process_observation(self, obs):
        if self.grayscale:
            if cv2:
                obs = cv2.cvtColor(obs, cv2.COLOR_RGB2GRAY)
                obs = cv2.resize(obs, (self.obs_size[1], self.obs_size[0]), interpolation=cv2.INTER_AREA)
            else:
                obs = obs.mean(axis=2).astype(np.uint8)
                obs = self._resize_nearest(obs)
            return np.expand_dims(obs, axis=0)

        if cv2:
            obs = cv2.resize(obs, (self.obs_size[1], self.obs_size[0]), interpolation=cv2.INTER_AREA)
        else:
            obs = self._resize_nearest(obs)
        return np.transpose(obs, (2, 0, 1))

    def _resize_nearest(self, obs):
        target_h, target_w = self.obs_size
        y_index = np.linspace(0, obs.shape[0] - 1, target_h).astype(int)
        x_index = np.linspace(0, obs.shape[1] - 1, target_w).astype(int)
        return obs[y_index][:, x_index]

    @staticmethod
    def _player_x(ram) -> int:
        return int(ram[0x94]) + (int(ram[0x95]) << 8)

    @staticmethod
    def _is_dead(ram) -> bool:
        return int(ram[0x71]) in (0x09, 0x0B)

    @staticmethod
    def _is_won(ram) -> bool:
        return int(ram[0x1493]) > 0
