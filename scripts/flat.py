import brownie
from brownie import StrategyCompLevUsdc


def main():
    my_contract = StrategyCompLevUsdc

    flattened_source = ""
    for name in my_contract._build["dependencies"]:
        build_json = my_contract._project._build.get(name)
        offset = slice(*build_json["offset"])
        source = build_json["source"][offset]
        flattened_source = f"{flattened_source}\n\n{source}"

    build_json = my_contract._build
    version = build_json["compiler"]["version"]
    offset = slice(*build_json["offset"])
    source = build_json["source"][offset]
    flattened_source = f"pragma solidity {version};{flattened_source}\n\n{source}\n"

    f = open("flat.sol", "w")
    f.write(flattened_source)
    f.close()