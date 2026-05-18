import torch
from stable_baselines3 import PPO


def linear_lr_schedule(progress_remaining: float) -> float:
    return 2.5e-5 + (2.5e-4 - 2.5e-5) * progress_remaining


class ModelWrapper:
    def __call__(self, venv):
        device = "cuda" if torch.cuda.is_available() else "cpu"

        return PPO(
            policy="CnnPolicy",
            device=device,
            env=venv,
            verbose=0,
            n_steps=2048,
            batch_size=2048,
            n_epochs=6,
            gamma=0.995,
            gae_lambda=0.95,
            learning_rate=linear_lr_schedule,
            ent_coef=0.002,
            vf_coef=0.5,
            clip_range=0.2,
            max_grad_norm=0.5,
            target_kl=0.03,
            policy_kwargs={
                "net_arch": {
                    "pi": [256, 256],
                    "vf": [256, 256],
                }
            },
        )
