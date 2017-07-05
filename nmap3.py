import socket, struct, nmap, inspect
from pathlib import Path
import os.path

''' Information found at http://xael.org/pages/python-nmap-en.html '''

# arguments = "-sN"
# arguments = "-sT"  # TCP Connect Scan (no root)
arguments = "-sL"  # Identify Host names (no root)

# arguments = "-F" # Fast Scanner
# arguments = "-T4 -A" #
# arguments = "-O" # Identify the Operating System of a host (requires root)
#  arguments = "-O"  # Find MAC

admin_testing = Path("csc.txt")


def starting():
    nm = nmap.PortScanner()
    nm.scan(hosts='{}/24'.format(get_default_gateway_linux()), arguments=arguments, sudo=True)

    print("Results:")

    if admin_testing:
        print("completed")
        return admin_testing

    else:
        for x in nm.all_hosts():
            if x not in get_default_gateway_linux():
                print("{}".format(x))

        return "csc.txt"


def get_default_gateway_linux():
    """ Read the default gateway directly from /proc. """
    with open("/proc/net/route") as fh:
        for line in fh:
            fields = line.strip().split()
            if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                continue

            return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))


def location_saved_results(memory_items):
    if admin_testing:
        current_directory = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
        path = "{}/{}".format(current_directory, admin_testing)

        if os.path.isfile(path):
            print("...file found...reading results")
            return path
        else:
            print("...file not found..exiting")
            exit()
    else:
        print(memory_items)


def filter_names(file):
    tag = "for "
    list_ip = {}
    final_result = []

    f = open(file, 'r')

    for each in f.readlines()[2:-1]:
        pos_count = len(tag) + 1
        pos_each = each.index(" for ")

        # print(each[pos_each+pos_count:])
        x = each[pos_each + pos_count:]

        if x[0].isdigit():
            '''
                Look for None assigned device names

                Examples:
                    10.228.76.115
                    comccsp076116.co.trinity-health.org (10.228.76.116)
            '''
            ip = x.rstrip().split(".")
            device = "DHCP"

            list_ip['IP'] = ip
            list_ip['Device'] = device

        else:
            ''' Need to replace ')' and '(' '''
            pos_device_assigned_ip = x.index("(") + 1  # remove white space and octets
            ip = x[pos_device_assigned_ip:-2]  # clean the ip address

            device_name_domain = x.rstrip().split(".")  # remove the domain from device name
            # [print(x) for x in device_name_domain if x.isdigit()]

            #  print("{}, {}".format(cleaned_ip.rstrip().split("."), device_name_domain[0]))
            list_ip["IP"] = ip.rstrip().split(".")
            list_ip["Device"] = device_name_domain[0]

        final_result.append(list_ip.copy())
    return final_result


if __name__ == '__main__':
    print("Pulling gateway={}".format(get_default_gateway_linux()))

    scanned_results = starting()

    s = location_saved_results(scanned_results)

    #  print(s.read())
    r = filter_names(s)
    for each in r:

        if each['Device'] is not str("DHCP"):
            print("{} - {}".format(each['IP'], each['Device']))

        else:
            print(each['IP'])
