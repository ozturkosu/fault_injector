from fault_injector.workload_generator.workload_generator import WorkloadGenerator
from scipy.stats import norm, exponweib
import datetime, calendar


# The list of fault commands to be injected.
# It is suggested to always use FULL paths, to avoid relative path issues
faults = ['faultlib/leak {0}',
          'faultlib/leak {0} l',
          'faultlib/memeater {0}',
          'faultlib/memeater {0} l',
          'faultlib/dial {0}',
          'faultlib/dial {0} l']

# The list of benchmarks to be used
benchmarks = ['faultlib/linpack',
              'faultlib/stream',
              'faultlib/generic']

# Input file on which fitting must be performed
in_path = 'workloads/pnnl_event_trace.csv'
# Output path of the generated workload
out = 'workloads/gen_workload.csv'
# Maximum time span (in seconds) of the workload
span = 3600 * 48


# Parsing the input data, which has a custom CSV format
def parse_data(path):
    in_file = open(path, 'r', errors='ignore')
    data = []
    for line in in_file:
        entry = line.split(',')
        if len(entry) > 0 and '/' in entry[0] and ':' in entry[0]:
            entry = entry[0].strip()
            # Converting the datetimes of the entries in UTC timestamps
            date_obj = datetime.datetime.strptime(entry, "%m/%d/%Y %H:%M")
            data.append(calendar.timegm(date_obj.utctimetuple()))
    in_file.close()
    data.sort()
    data_filtered = []
    # Calculating the difference between consecutive entries, i.e. fault inter-arrival times
    for i in range(1, len(data)):
        point = data[i] - data[i - 1]
        if point > 60:
            data_filtered.append(point)
    return data_filtered


if __name__ == '__main__':
    # Acquiring fault inter-arrival time data from a real fault trace
    data = parse_data(in_path)
    generator = WorkloadGenerator(path=out)
    # We set the fault generator so that a Normal distribution is used for the durations, and a Weibull distribution is
    # used for the inter-fault times
    generator.faultDurGenerator.set_distribution(norm(loc=60, scale=6))
    # Fitting a distribution over the acquired data
    generator.faultTimeGenerator.fit_data(exponweib, data)
    generator.faultTimeGenerator.show_fit(val_range=(0, 1000), n_bins=20)
    # We let the workload generator set the benchmark generator automatically, by imposing that roughly 80%
    # of the workload time must be spent in "busy" operation
    generator.autoset_bench_generators(busy_time=0.8, num_tasks=20, span_limit=span)
    # We start the workload generation process
    generator.generate(faults, benchmarks, span_limit=span)

    exit()
