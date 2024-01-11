import os
import random
import string

random_data_type = os.environ.get("RANDOM_DATA_TYPE", "string")
random_data_string_size = int(os.environ.get("RANDOM_DATA_STRING_SIZE", "12"))

exp_ciphers = os.environ.get("EXP_CIPHERS", "").split(",")
exp_sizes = list(map(int, os.environ.get("EXP_SIZES", "0").split(",")))
exp_samples = int(os.environ.get("EXP_SAMPLES", "0"))


def generate_random_temperature():
    min_temperature = -10.0
    max_temperature = 40.0

    random_temperature = round(random.uniform(min_temperature, max_temperature), 2)
    return random_temperature


def generate_random_humidity():
    min_humidity = 0.0
    max_humidity = 100.0

    random_humidity = round(random.uniform(min_humidity, max_humidity), 2)
    return random_humidity


def generate_random_pressure():
    min_pressure = 900.0
    max_pressure = 1100.0

    random_pressure = round(random.uniform(min_pressure, max_pressure), 2)
    return random_pressure


def generate_random_sensor_data():
    temperature = generate_random_temperature()
    humidity = generate_random_humidity()
    pressure = generate_random_pressure()

    return {
        "temperature": temperature,
        "humidity": humidity,
        "pressure": pressure
    }


def generate_random_string_data(size):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(size))


def x_y_z(indeks, size_x, size_y, size_z):
    z = indeks // (size_x * size_y)
    indeks -= (z * size_x * size_y)
    y = indeks // size_x
    x = indeks % size_x
    return x, y, z


def total_exp_data_size():
    return len(exp_ciphers) * len(exp_sizes) * exp_samples


def generate_exp_data(counter, has_data):
    cipher_index, size_index, sample_index = x_y_z(counter, len(exp_ciphers), len(exp_sizes), exp_samples)
    cipher = exp_ciphers[cipher_index]
    size = exp_sizes[size_index]
    sample = exp_samples
    data = {
        "cipher": cipher,
        "size": size,
        "sample": sample
    }
    if has_data is True:
        data["data"] = generate_random_string_data(size)
    return data


def generate_random_data_by_data_type(counter):
    if random_data_type == "temperature":
        return generate_random_temperature()
    elif random_data_type == "humidity":
        return generate_random_humidity()
    elif random_data_type == "pressure":
        return generate_random_pressure()
    elif random_data_type == "string":
        return generate_random_string_data(random_data_string_size)
    elif random_data_type == "exp":
        return generate_exp_data(counter, True)
    else:
        return None
