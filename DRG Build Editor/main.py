import mysql.connector
from mysql.connector import Error
import pandas as pd
from decouple import config
from tabulate import tabulate
import textwrap
from dataclasses import dataclass


# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def create_server_connection(host_name, user_name, user_password):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password
        )
        print("MySQL Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")

    return connection


def create_db_connection(host_name, user_name, user_password, db_name):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name
        )
        print("MySQL Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")

    return connection


# For SQL queries that change the database
def execute_query(connection, query, args=None):
    cursor = connection.cursor()
    try:
        cursor.execute(query, args)
        last_id = cursor.lastrowid;
        connection.commit()
        print("Query successful")
        return last_id
    except Error as err:
        print(f"Error: '{err}'")


# For SQL queries that don't change the database
def read_query(connection, query, args=None):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query, args)
        result = cursor.fetchall()
        return result
    except Error as err:
        print(f"Error: '{err}'")


def print_query(result, columns):
    ex_columns = ['Dwarf ID', 'Equipment ID', 'Grenade ID',
                  'Perk ID', 'Overclock ID', "Upgrade ID"]
    table = []
    for row in result:
        row = list(row)
        table.append(row)

    wrapper = textwrap.TextWrapper(width=50)
    for i in range(len(table)):
        for j in range(len(table[0])):
            if not isinstance(table[i][j], int):
                table[i][j] = wrapper.fill(text=table[i][j])

    df = pd.DataFrame(table, columns=columns)
    df.index += 1
    df = df.iloc[:, ~df.columns.isin(ex_columns)]
    print(tabulate(df, headers='keys', tablefmt='fancy_grid'))
    return table


def prompt_menu():
    menu = [[1, "Create New Build"],
            [2, "View Existing Builds"],
            [3, "View Dwarves"],
            [4, "View Perks"],
            [5, "Delete Build"],
            [6, "Quit"]]
    print(tabulate(menu, headers=["Input", "Option"], tablefmt="fancy_grid"))
    return input("Pick a Choice: ")


def selection_list(connection, query, columns, args=None):
    from_db = []
    result = read_query(connection, query, args)

    if not result:
        return -1

    from_db = print_query(result, columns)
    if len(from_db) == 1:
        print("Only one option:", from_db[0][1])
        return from_db[0][0]

    choice = choice = input("Pick a Choice: ")
    while not choice.isdigit():
        print("Must be a number")
        choice = choice = input("Pick a Choice: ")
    choice_num = int(choice)

    while choice_num <= 0 or choice_num > len(from_db):
        print("Input is not within bounds")
        choice = input("Pick a Choice: ")
        choice_num = int(choice)
    query_id = from_db[choice_num-1][0]
    print("ID:", query_id)
    print("You have Chosen:", from_db[choice_num-1][1])
    return int(query_id)


def get_equipment(connect, dwarf, type):
    equipment_attributes = ["Equipment ID", "Equipment Name", "Equipment Description"]
    equipment_select = """
        SELECT equipment_id, equipment_name, equipment_desc
        FROM equipment
        WHERE dwarf_id = {} and equipment_type = '{}'
        """.format(dwarf, type)

    equipment = selection_list(connect, equipment_select, equipment_attributes)
    return equipment


def get_upgrades(connect, equipment, select):
    attributes = ["Upgrade ID", "Upgrade Name", "Equipment Name", "Upgrade Description"]
    num_upgrade = read_query(connect, """
        SELECT num_tiers
        FROM equipment WHERE
        equipment_id = {}
        """.format(equipment))
    print("Number of Upgrade Tiers:", num_upgrade[0][0])
    upgrades = []
    for i in range(num_upgrade[0][0]):
        upgrade_select = """
        SELECT upgrade.upgrade_id, upgrade.upgrade_name, equipment.equipment_name, upgrade.upgrade_desc
        FROM upgrade
        INNER JOIN equipment ON upgrade.equipment_id = equipment.equipment_id
        WHERE upgrade.equipment_id = {} and upgrade.tier_number = {}
        """.format(equipment, i+1)
        print("Upgrade Tier:", i+1)
        if select:
            upgrade = selection_list(connect, upgrade_select, attributes)
        elif not select:
            upgrade = read_query(connect, upgrade_select)
            print_query(upgrade, attributes)
        upgrades.append(upgrade)
    return upgrades


def get_overclock(connect, equipment, select):
    attributes = ["Overclock ID", "Overclock Name", "Overclock Type", "Overclock Description"]
    overclock_select = """
    SELECT overclock_id, overclock_name, overclock_type, overclock_desc
    FROM overclock
    WHERE weapon_id = {}
    """.format(equipment)
    if select:
        overclock = selection_list(connect, overclock_select, attributes)
    elif not select:
        overclock = read_query(connect, overclock_select)
        print_query(overclock, attributes)
    return overclock


def choose_perk(connect, perk_type, perks, select):

    string_ints = [str(perk) for perk in perks]
    perk_string = ','.join(string_ints)

    attributes = ["Perk ID", "Perk Name", "Perk Type", "Perk Description"]
    if not perks:
        perk_select = '''
            SELECT perk_id, perk_name, perk_type, perk_desc
            FROM perk
            WHERE perk_type = '{}'
            '''.format(perk_type)

    else:
        perk_select = '''
                    SELECT perk_id, perk_name, perk_type, perk_desc
                    FROM perk
                    WHERE perk_type = '{}' AND perk_id NOT IN ({})
                    '''.format(perk_type, perk_string)
    if select:
        perk = selection_list(connect, perk_select, attributes)
    elif not select:
        perk = read_query(connect, perk_select)
        print_query(perk, attributes)
    return perk


def get_perks(connect):
    passive_perks = []
    for i in range(3):
        passive = choose_perk(connect, "passive", passive_perks, True)
        passive_perks.append(passive)

    print(passive_perks)

    active_perks = []
    for i in range(2):
        active = choose_perk(connect, "active", active_perks, True)
        active_perks.append(active)

    print(active_perks)

    perks = passive_perks + active_perks
    return perks


def display_build():
    print("Displaying Build")


def insert_manytomany(connect, table, column, build, other_id):
    many_sql = '''
    INSERT INTO {} (build_id, {})
        VALUES ({}, {})
    '''.format(table, column, build, other_id)

    execute_query(connect, many_sql)


def create_build(connect):
    confirm = 'n'
    dwarf_select = """
    SELECT dwarf_id, dwarf_name, dwarf_desc
    FROM dwarf;
    """

    while confirm != 'y':

        print("Create a name for this build.")
        name = input()

        print("Who created this build?")
        author = input()

        print("Insert a description for this build")
        description = input()

        dwarf_attributes = ["Dwarf ID", "Dwarf Name", "Dwarf Description"]
        dwarf = selection_list(connect, dwarf_select, dwarf_attributes)

        grenade_select = """
        SELECT grenade_id, grenade_name, grenade_desc
        FROM grenade 
        WHERE dwarf_id = {}""".format(dwarf)

        primary = get_equipment(connect, dwarf, 'primary')
        primary_upgrades = get_upgrades(connect, primary, True)
        primary_overclock = get_overclock(connect, primary, True)

        secondary = get_equipment(connect, dwarf, 'secondary')
        secondary_upgrades = get_upgrades(connect, secondary, True)
        secondary_overclock = get_overclock(connect, secondary, True)

        mobility = get_equipment(connect, dwarf, 'mobility')
        mobility_upgrades = get_upgrades(connect, mobility, True)

        support = get_equipment(connect, dwarf, 'support')
        support_upgrades = get_upgrades(connect, support, True)

        armor = get_equipment(connect, dwarf, 'armor')
        armor_upgrades = get_upgrades(connect, armor, True)

        grenade_attributes = ["Grenade ID", "Grenade Name", "Grenade Description"]
        grenade = selection_list(connect, grenade_select, grenade_attributes)

        perks = get_perks(connect)

        flag = False

        while not flag:
            print("(y) This build looks good!")
            print("(n) Hold on, I messed up")
            confirm = input()
            if confirm != 'y' and confirm != 'n':
                print("Invalid input, choose y or n")
            else:
                flag = True

    print("Saving Build!")
    build_sql = '''
    INSERT INTO build (build_id, build_name, 
    build_author, build_desc, dwarf_id, 
    grenade_id)
        VALUES (NULL, %s, %s, %s, %s, %s)
        '''
    args = name, author, description, dwarf, grenade

    build_id = execute_query(connect, build_sql, args)

    insert_manytomany(connect, "build_equipment", "equipment_id", build_id, primary)
    insert_manytomany(connect, "build_equipment", "equipment_id", build_id, secondary)
    insert_manytomany(connect, "build_equipment", "equipment_id", build_id, mobility)
    insert_manytomany(connect, "build_equipment", "equipment_id", build_id, support)
    insert_manytomany(connect, "build_equipment", "equipment_id", build_id, armor)
    insert_manytomany(connect, "build_overclock", "overclock_id", build_id, primary_overclock)
    insert_manytomany(connect, "build_overclock", "overclock_id", build_id, secondary_overclock)

    for i in range(len(primary_upgrades)):
        insert_manytomany(connect, "build_upgrade", "upgrade_id", build_id, primary_upgrades[i])
    for i in range(len(secondary_upgrades)):
        insert_manytomany(connect, "build_upgrade", "upgrade_id", build_id, secondary_upgrades[i])
    for i in range(len(mobility_upgrades)):
        insert_manytomany(connect, "build_upgrade", "upgrade_id", build_id, mobility_upgrades[i])
    for i in range(len(support_upgrades)):
        insert_manytomany(connect, "build_upgrade", "upgrade_id", build_id, support_upgrades[i])
    for i in range(len(armor_upgrades)):
        insert_manytomany(connect, "build_upgrade", "upgrade_id", build_id, armor_upgrades[i])

    for i in range(len(perks)):
        insert_manytomany(connect, "build_perk", "perk_id", build_id, perks[i])

    print("ID of recently made build:", build_id)

    print("Build Successfully Created!")


def combine_builds(connect, build, external, id):
    from_db = []
    join_builds = '''
        SELECT
            {}.{}_name
        FROM build
        JOIN {} ON build.build_id = {}.build_id
        JOIN {} ON {}.{}_id = {}.{}_id
        WHERE build.build_id = {}
        '''.format(external, external, build, build, external, external, external, build, external, id)
    result = read_query(connect, join_builds)

    for row in result:
        row = row
        from_db.append(row[0])
    return from_db


def view_build_dwarves(connect, dwarf_id):
    attributes = ["build_id", "build_name", "build_author"]

    build_select = '''
    SELECT build_id, build_name, build_author
    FROM build
    WHERE dwarf_id = {}
    '''.format(dwarf_id)

    build = selection_list(connect, build_select, attributes)
    return build


def equipment_print(equipment_name, overclocks, upgrades, labels, type):

    data = [equipment_name]
    if type == "primary":
        data.append(overclocks[0])
    elif type == "secondary":
        data.append(overclocks[1])
    for i in range(len(upgrades)):
        if upgrades[i][2] == type:
            data.append(upgrades[i][0])

    table = []
    for i in range(len(data)):
        table.append([labels[i], data[i]])
    print(tabulate(table, headers=[type.capitalize(), 'Name'], tablefmt='fancy_grid'))


def split_upgrades(connect, id):
    join_builds = '''
        SELECT
            upgrade.upgrade_name,
            upgrade.upgrade_desc,
            equipment.equipment_type
        FROM build
        JOIN build_upgrade ON build.build_id = build_upgrade.build_id
        JOIN upgrade ON upgrade.upgrade_id = build_upgrade.upgrade_id
        JOIN equipment ON equipment.equipment_id = upgrade.equipment_id
        WHERE build.build_id = {}
        '''.format(id)
    result = read_query(connect, join_builds)
    return result


def get_num_tiers(connect, equipment):
    tier_select = '''
    SELECT num_tiers
    FROM equipment
    WHERE equipment_name = '{}'
    '''.format(equipment)
    tier_number = read_query(connect, tier_select)
    return int(tier_number[0][0])


def print_other(connect, start_label, equipment, equip_index, overclocks, upgrades, type):
    labels = ["{} Tool".format(type.capitalize())]
    mobility_tiers = get_num_tiers(connect, equipment[equip_index])
    for i in range(mobility_tiers):
        labels.append("{} Upgrade {}".format(type.capitalize(), i+1))
    equipment_print(equipment[equip_index], overclocks, upgrades, labels, type)


def view_build(connect):
    dwarf_select = """
    SELECT dwarf_id, dwarf_name
    FROM dwarf;
    """
    dwarf_attributes = ["dwarf_id", "dwarf_name"]

    dwarf = selection_list(connect, dwarf_select, dwarf_attributes)
    build = view_build_dwarves(connect, dwarf)
    if build == -1:
        print("There are no builds for this class")
        return

    build_query = '''
    SELECT
        build_name,
        build_author,
        build_desc,
        dwarf_name,
        grenade_name
    FROM build
    JOIN dwarf ON build.dwarf_id=dwarf.dwarf_id
    JOIN grenade ON build.grenade_id=grenade.grenade_id
    WHERE build.build_id = {}
    '''.format(build)

    build_labels = ["Build Name", "Build Author", "Build Description", "Dwarf", "Grenade"]
    build_list = read_query(connect, build_query)
    build_data = []
    for row in build_list:
        row = list(row)
        build_data.append(row)

    build_table = []
    for i in range(len(build_data[0])):
        build_table.append([build_labels[i], build_data[0][i]])

    print(tabulate(build_table, headers=["Build", "Name"], tablefmt="fancy_grid"))

    equipment = combine_builds(connect, "build_equipment", "equipment", build)
    overclocks = combine_builds(connect, "build_overclock", "overclock", build)
    perks = combine_builds(connect, "build_perk", "perk", build)
    upgrades = split_upgrades(connect, build)

    primary_labels = ["Primary Weapon", "Primary Overclock",
                      "Primary Upgrade 1", "Primary Upgrade 2",
                      "Primary Upgrade 3", "Primary Upgrade 4",
                      "Primary Upgrade 5"]
    equipment_print(equipment[0], overclocks, upgrades, primary_labels, "primary")

    secondary_labels = ["Secondary Weapon", "Secondary Overclock",
                        "Secondary Upgrade 1", "Secondary Upgrade 2",
                        "Secondary Upgrade 3", "Secondary Upgrade 4",
                        "Secondary Upgrade 5"]

    equipment_print(equipment[1], overclocks, upgrades, secondary_labels, "secondary")

    print_other(connect, "Mobility Tool", equipment, 2, overclocks, upgrades, "mobility")

    print_other(connect, "Support Tool", equipment, 3, overclocks, upgrades, "support")

    print_other(connect, "Armor", equipment, 4, overclocks, upgrades, "armor")

    perk_labels = ["Passive", "Passive", "Passive", "Active", "Active"]
    perk_table = []
    for i in range(len(perks)):
        perk_table.append([perk_labels[i], perks[i]])
    print(tabulate(perk_table, headers=["Perk", "Name"], tablefmt='fancy_grid'))


def view_dwarves(connect):
    dwarf_select = """
        SELECT *
        FROM dwarf;
        """
    dwarf_attributes = ["Dwarf ID", "Dwarf Name", "Dwarf Description"]
    dwarf = selection_list(connect, dwarf_select, dwarf_attributes)

    menu = [[1, "Primary Weapons"],
            [2, "Secondary Weapons"],
            [3, "Mobility Tool"],
            [4, "Support Tool"],
            [5, "Armor"],
            [6, "Go Back"]]

    choice = "0"
    while choice != "6":
        print(tabulate(menu, headers=["Input", "Option"], tablefmt="fancy_grid"))
        choice = input("Pick a Choice: ")
        if choice == "1":
            print("Primary")
            primary = get_equipment(connect, dwarf, 'primary')
            get_upgrades(connect, primary, False)
            get_overclock(connect, primary, False)
        elif choice == "2":
            print("Secondary")
            secondary = get_equipment(connect, dwarf, 'secondary')
            get_upgrades(connect, secondary, False)
            get_overclock(connect, secondary, False)
        elif choice == "3":
            print("Mobility")
            mobility = get_equipment(connect, dwarf, 'mobility')
            get_upgrades(connect, mobility, False)
        elif choice == "4":
            print("Support")
            support = get_equipment(connect, dwarf, 'support')
            get_upgrades(connect, support, False)
        elif choice == "5":
            print("Armor")
            armor = get_equipment(connect, dwarf, 'armor')
            get_upgrades(connect, armor, False)
        elif choice == "6":
            print("Going Back!")
        else:
            print("Invalid Choice")


def view_perks(connect):
    choose_perk(connect, "passive", [], False)
    choose_perk(connect, "active", [], False)


def delete_build(connect):
    dwarf_select = """
    SELECT dwarf_id, dwarf_name
    FROM dwarf;
    """
    dwarf_attributes = ["dwarf_id", "dwarf_name"]

    dwarf = selection_list(connect, dwarf_select, dwarf_attributes)
    build = view_build_dwarves(connect, dwarf)
    if build == -1:
        print("There are no builds for this class")
        return

    delete_query = '''
    DELETE
    FROM build
    WHERE build_id = {}
    '''.format(build)

    execute_query(connect, delete_query)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    db_connection = create_db_connection("localhost", "root", config("PASSWORD"), "deep rock galactic")

    user_input = 0
    while user_input != "5":
        user_input = prompt_menu()
        if user_input == "1":
            print("New Build")
            create_build(db_connection)
        elif user_input == "2":
            print(2)
            view_build(db_connection)
        elif user_input == "3":
            print(3)
            view_dwarves(db_connection)
        elif user_input == "4":
            print(4)
            view_perks(db_connection)
        elif user_input == "5":
            delete_build(db_connection)
        elif user_input == "6":
            print(6)
            print("Rock and Stone!")
            break
        else:
            print("Wrong Input, try again!")
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
