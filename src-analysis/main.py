import json
import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
import mysql.connector

connection = mysql.connector.connect(
    host=os.getenv('MYSQL_HOST', 'localhost'),
    port=int(os.getenv('MYSQL_PORT', '3306')),
    user=os.getenv('MYSQL_USER', 'zipkin'),
    password=os.getenv('MYSQL_USER', 'zipkin'),
    database=os.getenv('MYSQL_USER', 'zipkin'),
)

base_path = os.getenv("BASE_PATH", os.path.dirname(os.path.realpath(__file__)) + "/../analysis/").rstrip('/') + '/'

cursor = connection.cursor()

if os.path.exists(base_path + 'spans.pickle'):
    os.remove(base_path + 'spans.pickle')
if os.path.exists(base_path + 'services.pickle'):
    os.remove(base_path + 'services.pickle')
if os.path.exists(base_path + 'analysis.pickle'):
    os.remove(base_path + 'analysis.pickle')

if os.path.exists(base_path + 'spans.pickle'):
    with open(base_path + 'spans.pickle', 'rb') as file:
        rows = pickle.load(file)
else:
    cursor.execute('select trace_id from zipkin_spans group by trace_id')
    rows = cursor.fetchall()
    with open(base_path + 'spans.pickle', 'wb') as file:
        pickle.dump(rows, file)


if os.path.exists(base_path + 'services.pickle'):
    with open(base_path + 'services.pickle', 'rb') as file:
        services = pickle.load(file)
else:
    cursor.execute('select trace_id, span_id, a_value from zipkin_annotations where a_key="service.name"')
    services = cursor.fetchall()
    cservices = []
    for service in services:
        cservice = list(service)
        cservice[2] = cservice[2].decode('ascii')
        cservices.append(cservice)
    services = cservices
    with open(base_path + 'services.pickle', 'wb') as file:
        pickle.dump(services, file)


def get_span_id(trace_id, service_name):
    for service in services:
        if service[0] == trace_id and service[2] == service_name:
            return service[1]


def get_span_id2(trace_id, service_name):
    cursor.execute('select span_id from zipkin_annotations where trace_id = %s and a_key="service.name" and a_value=%s limit 1', (trace_id, service_name))
    return cursor.fetchone()[0]


def get_timing(trace_id, service_name):
    cursor.execute('select start_ts, duration from zipkin_spans where trace_id = %s and name = %s limit 1', (trace_id, service_name))
    return cursor.fetchone()


def get_all_values(trace_id, span_id):
    cursor.execute('select a_key, a_value from zipkin_annotations where trace_id = %s and span_id = %s', (trace_id, span_id))
    return cursor.fetchall()


def filter_values(values, key):
    return [value[1] for value in values if value[0] == key][0].decode('ascii')

analysis = {}
n = 0

for row in rows:
    n += 1
    print("Progress: " + str(n) + " / " + str(len(rows)))
    trace_id = row[0]
    # publisher-app-1
    publisher_app_1_span_id = get_span_id(trace_id, 'publisher-app-1')
    span_values = get_all_values(trace_id, publisher_app_1_span_id)
    encrypt_memory_usage = int(filter_values(span_values, 'peak_memory_usage'))
    publisher_raw_data_size = int(filter_values(span_values, 'raw_data_size'))
    encrypted_data_size = int(filter_values(span_values, 'encrypted_data_size'))
    encrypt_average_execution_time = float(filter_values(span_values, 'average_execution_time'))
    cipher_payload = json.loads(filter_values(span_values, 'cipher_payload'))
    cipher_algorithm = cipher_payload['algorithm']
    publisher_app_1_timing = get_timing(trace_id, 'publisher-app-1')
    # gateway-app-1
    # gateway_app_1_timing = get_timing(trace_id, 'gateway-app-1')
    # gateway-app-2
    # gateway_app_2_timing = get_timing(trace_id, 'gateway-app-2')
    # gateway-app-3
    # gateway_app_3_timing = get_timing(trace_id, 'gateway-app-3')
    # subscriber-app-1
    subscriber_app_1_span_id = get_span_id(trace_id, 'subscriber-app-1')
    span_values = get_all_values(trace_id, subscriber_app_1_span_id)
    decrypt_average_execution_time = float(filter_values(span_values, 'average_execution_time'))
    subscriber_raw_data_size = int(filter_values(span_values, 'raw_data_size'))
    decrypted_data_size = int(filter_values(span_values, 'decrypted_data_size'))
    decrypt_memory_usage = int(filter_values(span_values, 'peak_memory_usage'))
    cipher_payload = json.loads(filter_values(span_values, 'cipher_payload'))
    cipher_algorithm = cipher_payload['algorithm']
    subscriber_app_1_timing = get_timing(trace_id, 'subscriber-app-1')

    latency = subscriber_app_1_timing[0] - publisher_app_1_timing[0] + decrypt_average_execution_time

    if cipher_algorithm not in analysis:
        analysis[cipher_algorithm] = {}

    if publisher_raw_data_size not in analysis[cipher_algorithm]:
        analysis[cipher_algorithm][publisher_raw_data_size] = {}

    if "encrpytion_memory_usage" not in analysis[cipher_algorithm][publisher_raw_data_size]:
        analysis[cipher_algorithm][publisher_raw_data_size]["encrpytion_memory_usage"] = 0
    if "decrpytion_memory_usage" not in analysis[cipher_algorithm][publisher_raw_data_size]:
        analysis[cipher_algorithm][publisher_raw_data_size]["decrpytion_memory_usage"] = 0
    if "encrpytion_average_execution_time" not in analysis[cipher_algorithm][publisher_raw_data_size]:
        analysis[cipher_algorithm][publisher_raw_data_size]["encrpytion_average_execution_time"] = 0
    if "decrpytion_average_execution_time" not in analysis[cipher_algorithm][publisher_raw_data_size]:
        analysis[cipher_algorithm][publisher_raw_data_size]["decrpytion_average_execution_time"] = 0
    if "raw_data_size" not in analysis[cipher_algorithm][publisher_raw_data_size]:
        analysis[cipher_algorithm][publisher_raw_data_size]["raw_data_size"] = 0
    if "encrypted_data_size" not in analysis[cipher_algorithm][publisher_raw_data_size]:
        analysis[cipher_algorithm][publisher_raw_data_size]["encrypted_data_size"] = 0
    if "latency" not in analysis[cipher_algorithm][publisher_raw_data_size]:
        analysis[cipher_algorithm][publisher_raw_data_size]["latency"] = 0
    if "count" not in analysis[cipher_algorithm][publisher_raw_data_size]:
        analysis[cipher_algorithm][publisher_raw_data_size]["count"] = 0

    analysis[cipher_algorithm][publisher_raw_data_size]["encrpytion_memory_usage"] += encrypt_memory_usage
    analysis[cipher_algorithm][publisher_raw_data_size]["decrpytion_memory_usage"] += decrypt_memory_usage
    analysis[cipher_algorithm][publisher_raw_data_size]["encrpytion_average_execution_time"] += encrypt_average_execution_time
    analysis[cipher_algorithm][publisher_raw_data_size]["decrpytion_average_execution_time"] += decrypt_average_execution_time
    analysis[cipher_algorithm][publisher_raw_data_size]["raw_data_size"] += publisher_raw_data_size
    analysis[cipher_algorithm][publisher_raw_data_size]["encrypted_data_size"] += encrypted_data_size
    analysis[cipher_algorithm][publisher_raw_data_size]["latency"] += latency * 1e-6
    analysis[cipher_algorithm][publisher_raw_data_size]["count"] += 1


for cipher_algorithm in analysis:
    for publisher_raw_data_size in analysis[cipher_algorithm]:
        c = analysis[cipher_algorithm][publisher_raw_data_size]["count"]
        analysis[cipher_algorithm][publisher_raw_data_size]["encrpytion_memory_usage"] /= c
        analysis[cipher_algorithm][publisher_raw_data_size]["decrpytion_memory_usage"] /= c
        analysis[cipher_algorithm][publisher_raw_data_size]["encrpytion_average_execution_time"] /= c
        analysis[cipher_algorithm][publisher_raw_data_size]["decrpytion_average_execution_time"] /= c
        analysis[cipher_algorithm][publisher_raw_data_size]["raw_data_size"] /= c
        analysis[cipher_algorithm][publisher_raw_data_size]["encrypted_data_size"] /= c
        analysis[cipher_algorithm][publisher_raw_data_size]["latency"] /= c
        analysis[cipher_algorithm][publisher_raw_data_size]["data_change_rate"] = analysis[cipher_algorithm][publisher_raw_data_size]["encrypted_data_size"] / analysis[cipher_algorithm][publisher_raw_data_size]["raw_data_size"]

with open(base_path + 'analysis.pickle', 'wb') as file:
    pickle.dump(analysis, file)

with open(base_path + 'analysis.json', 'w', encoding="utf-8") as file:
    json.dump(analysis, file, ensure_ascii=False, indent=4)

with open(base_path + 'analysis.pickle', 'rb') as file:
    analysis = pickle.load(file)

for cipher_algorithm in analysis:
    for size in analysis[cipher_algorithm]:
        analysis[cipher_algorithm][size]["data_change_rate"] = 100 * (analysis[cipher_algorithm][size]["data_change_rate"] - 1)
        analysis[cipher_algorithm][size]["latency"] = 1e3 * analysis[cipher_algorithm][size]["latency"]
        analysis[cipher_algorithm][size]["encrpytion_average_execution_time"] = 1e6 * analysis[cipher_algorithm][size]["encrpytion_average_execution_time"]
        analysis[cipher_algorithm][size]["decrpytion_average_execution_time"] = 1e6 * analysis[cipher_algorithm][size]["decrpytion_average_execution_time"]


def plot_analysis(analysis, key, title="", xlabel="", ylabel=""):
    data = {}
    sizes = []
    comparison = {}
    for cipher_algorithm in analysis:
        for size in analysis[cipher_algorithm]:
            if size not in sizes:
                sizes.append(size)
    sizes.sort()
    for cipher_algorithm in analysis:
        for size in sizes:
            if cipher_algorithm not in data:
                data[cipher_algorithm] = []
            data[cipher_algorithm].append(analysis[cipher_algorithm][size][key])
            if size not in comparison:
                comparison[size] = []
            comparison[size].append((cipher_algorithm, analysis[cipher_algorithm][size][key]))

    print("Comparison: " + key)
    for size in comparison:
        comparison[size].sort(key=lambda x: x[1])
        comparison_row = "Size: " + str(size) + ": "
        for i in range(len(comparison[size])):
            comparison_row += comparison[size][i][0] + ", "
        print(comparison_row)

    index = np.arange(len(sizes))
    bar_width = 0.1
    fig, ax = plt.subplots()
    i = 0
    for cipher_algorithm in data:
        ax.bar(index + i * bar_width, data[cipher_algorithm], bar_width, label=cipher_algorithm)
        i += 1
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_xticks(index + bar_width / 2)
    ax.set_xticklabels(sizes)
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize="small")
    plt.savefig(base_path + title + ".png", dpi=300)
    plt.show()
    plt.close()
    print()


plot_analysis(analysis, "data_change_rate", title="Data Growth Rate", xlabel="Data Size", ylabel="Data Growth Rate (%)")
plot_analysis(analysis, "encrpytion_memory_usage", title="Encryption Memory Usage", xlabel="Data Size", ylabel="Memory Usage (Bytes)")
plot_analysis(analysis, "decrpytion_memory_usage", title="Decryption Memory Usage", xlabel="Data Size", ylabel="Memory Usage (Bytes)")
plot_analysis(analysis, "encrpytion_average_execution_time", title="Encryption Average Execution Time", xlabel="Data Size", ylabel="Average Execution Time (µs)")
plot_analysis(analysis, "decrpytion_average_execution_time", title="Decryption Average Execution Time", xlabel="Data Size", ylabel="Average Execution Time (µs)")
plot_analysis(analysis, "latency", title="Latency", xlabel="Data Size", ylabel="Latency (ms)")

print("Analysis completed!")
