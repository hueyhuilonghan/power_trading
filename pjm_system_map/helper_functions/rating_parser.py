import re

import pandas as pd


# UNTESTED SCRIPT

def parseRating(OTHER_DATA_DIRECTORY, CACHE_DATA_DIRECTORY):
    """
    function to parse raw rating txt file from PJM to csv, which is
        more digestible.
    """
    inputFilePath = os.path.join(OTHER_DATA_DIRECTORY, "ratings.txt")
    outputFilePath = os.path.join(CACHE_DATA_DIRECTORY, "ratings.csv")

    df_dict = {"company": [], "substation": [], "voltage": [],
               "device": [], "end": [], "description": [],
               "degreef": [], "day_normal": [], "day_long": [], "day_short": [],
               "night_normal": [], "night_long": [], "night_short": [], "night_dump": []
              }

    with open(inputFilePath, "r") as f:
        company = None
        substation = None
        voltage = None
        device = None
        end = None
        description = None

        for line in f:

            if re.match(r"^-{20}\sCompany:\s([\w-]+)\s-{20}$", line):
                s = re.search(r"^-{20}\sCompany:\s([\w-]+)\s-{20}", line)
                company = s.group(1).strip()

            elif re.match(r"^Substn:\s([\w\s-]+)\skV:\s(\d+)\sKV\s+Dev:\s(.*)\s+End:\s(.*)$", line):
                s = re.search(r"^Substn:\s([\w\s-]+)\skV:\s(\d+)\sKV\s+Dev:\s(.*)\s+End:\s(.*)$", line)
                substation = s.group(1).strip()
                voltage = s.group(2).strip()
                device = s.group(3).strip()
                end = s.group(4).strip()

            elif re.match(r"^\sDescr:\s(.*)\s+$", line):
                s = re.search(r"^\sDescr:\s(.*)\s+$", line)
                description = s.group(1).strip()

            elif re.match(r"^\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)", line):
                nums = line.split()
                if(len(nums) != 9):
                    raise("Unrecognized number of numbers!")

                # append to dict
                df_dict["company"].append(company)
                df_dict["substation"].append(substation)
                df_dict["voltage"].append(voltage)
                df_dict["device"].append(device)
                df_dict["end"].append(end)
                df_dict["description"].append(description)
                df_dict["degreef"].append(nums[0])
                df_dict["day_normal"].append(nums[1])
                df_dict["day_long"].append(nums[2])
                df_dict["day_short"].append(nums[3])
                df_dict["night_normal"].append(nums[4])
                df_dict["night_long"].append(nums[5])
                df_dict["night_short"].append(nums[6])
                df_dict["night_dump"].append(nums[7])

            elif re.match(r"^\s+-------- Day ---------  -------- Night -------$", line):
                continue

            elif re.match(r"^Degf  Norm  Long  Shrt  Dump  Norm  Long  Shrt  Dump$", line):
                continue

            else:
                continue


    df = pd.DataFrame(df_dict)

    if df.shape[0] != df.drop_duplicates().shape[0]:
        raise("There are duplicates")

    tmp = df.groupby(["company", "substation", "voltage", "device", "end", "description"]).size()
    if len(tmp[tmp != 8]) != 0:
        raise(ValueError("There are component that has abnormal rating amount"))

    df.to_csv(outputFilePath, index=False)
