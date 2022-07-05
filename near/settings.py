from pydantic import Extra


class NearConfig:
    env_file = "./env/near.env"
    env_file_encoding = "utf-8"
    extra = Extra.allow
