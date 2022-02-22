from chrisomatic.spec.deserialize import deserialize_config


def apply(input_config: str):
    # config = deserialize_config(config_path)
    # config = deserialize_config(input_config)
    # print(config)
    config = deserialize_config(input_config)
    print(config)


