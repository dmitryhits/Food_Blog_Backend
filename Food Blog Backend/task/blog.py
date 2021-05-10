import sqlite3
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('database')
parser.add_argument("--ingredients")
parser.add_argument("--meals")

conn = sqlite3.connect('food_blog.db')
food_cursor = conn.cursor()
table_names = ['meals', 'ingredients', 'measures']

create_recipes_table = ('\n'
                        'create table if not exists recipes (\n'
                        'recipe_id integer primary key,\n'
                        'recipe_name varchar(100) not null,\n'
                        'recipe_description varchar(1000));')

table_columns = dict(meals=('meal_id', 'meal_name'),
                     ingredients=('ingredient_id', 'ingredient_name'),
                     measures=('measure_id', 'measure_name'))

table_data = dict(meals=("breakfast", "brunch", "lunch", "supper"),
                  ingredients=("milk", "cacao", "strawberry", "blueberry", "blackberry", "sugar"),
                  measures=("ml", "g", "l", "cup", "tbsp", "tsp", "dsp", ""))

for table, columns in table_columns.items():
    # food_cursor.execute(f'drop table {table};')
    not_null = 'not null'
    if table == 'measures':
        not_null = ''
    sql_line = (f"create table if not exists {table} \n"
                f"    ({columns[0]}  integer primary key,{columns[1]} varchar(30) unique {not_null});")
    food_cursor.execute(sql_line)

food_cursor.execute(create_recipes_table)

for name, entries in table_data.items():
    insert_line = f'INSERT OR IGNORE INTO {name} ({table_columns[name][1]}) VALUES '
    for entry in entries:
        insert_line += f"('{entry}'), "
    else:
        insert_line = insert_line.removesuffix(', ')
        insert_line += ';'
    # print(insert_line)
    food_cursor.execute(insert_line)

conn.commit()
count = food_cursor.execute('SELECT COUNT(*) FROM measures').fetchone()[0]


# print(count)


def recipe_input(cursor, measures, ingredient):
    while True:
        print('Pass the empty recipe name to exit.')
        recipe_name = input('Recipe name:')
        if not recipe_name:
            break
        recipe_description = input('Recipe description:')
        sql_query = f"""insert into recipes (recipe_name, recipe_description) 
        values ('{recipe_name}', '{recipe_description}')"""
        recipe_id = cursor.execute(sql_query).lastrowid
        result = cursor.execute('SELECT * FROM meals')
        line = ''
        for item in result.fetchall():
            line += f"{item[0]}) {item[1]} "
        # print(line)
        meal_ids = (int(i) for i in input("When the dish can be served:").split())
        for meal_id in meal_ids:
            insert_serve_choices = f'insert into serve (recipe_id, meal_id)\n' \
                                   f'values ({recipe_id}, {meal_id});'
            print(insert_serve_choices)
            cursor.execute(insert_serve_choices)
        get_ingredient(cursor, recipe_id, measures, ingredient)


def get_ingredient(cursor, recipe_id, measures, ingredients):
    measure_id = 0
    ingredient_id = 0
    quantity = 0
    while True:
        line = input("Input quantity of ingredient <press enter to stop>:")
        if not line:
            break
        else:
            parts = line.split()
            quantity = int(parts[0])
            if len(parts) == 3:
                ingredient_in = parts[2]
                measure_in = parts[1]
            else:
                ingredient_in = parts[1]
                measure_in = ''
            if measure_in:
                chosen_measures = [i for i in measures if i.startswith(measure_in)]
                if len(chosen_measures) > 1:
                    print("The measure is not conclusive!")
                    continue
                else:
                    measure_id = measures.index(chosen_measures[0]) + 1
                    # print('measure_id', measure_id)
            else:
                measure_id = len(measures)
            chosen_ingredients = [i for i in ingredients if i.startswith(ingredient_in)]
            if len(chosen_ingredients) > 1:
                print("The ingredient is not conclusive!")
                continue
            else:
                ingredient_id = ingredients.index(chosen_ingredients[0]) + 1
            insert_quantities = f'insert into quantity (quantity, recipe_id, measure_id, ingredient_id)\n' \
                                f'values ({quantity}, {recipe_id}, {measure_id}, {ingredient_id});'
            cursor.execute(insert_quantities)


# print('foreign keys')
food_cursor.execute("PRAGMA foreign_keys = ON;")

create_serve_table = f"create table if not exists serve (\n" \
                     f"serve_id integer primary key,\n" \
                     f"recipe_id integer not null,\n" \
                     f"meal_id integer not null,\n" \
                     f"foreign key (recipe_id) references recipes(recipe_id)," \
                     f"foreign key (meal_id) references meals(meal_id));"

food_cursor.execute(create_serve_table)
# print('serve created')
create_quantity_table = f"create table if not exists quantity (\n" \
                        f"quantity_id integer primary key, \n" \
                        f"quantity integer not null, \n" \
                        f"recipe_id integer not null, \n" \
                        f"measure_id integer not null, \n" \
                        f"ingredient_id integer not null, \n" \
                        f"foreign key (recipe_id) references recipes(recipe_id)," \
                        f"foreign key (measure_id) references measures(measure_id), " \
                        f"foreign key (ingredient_id) references ingredients(ingredient_id));"
food_cursor.execute(create_quantity_table)
# print('quantity created')

args = parser.parse_args()
# print('ars parsed')

if args.ingredients and args.meals:
    ingredients_list = "'" + "','".join(args.ingredients.split(',')) + "'"
    print(ingredients_list)
    meals_list = "'" + "','".join(args.meals.split(',')) + "'"
    print(meals_list)
    find_meal_ids = f"select meal_id from meals where meal_name in ({meals_list})"
    # q_result = food_cursor.execute(find_meal_ids)
    # print('meal_id', q_result.fetchall())
    find_ingredient_ids = f"select ingredient_id from ingredients where ingredient_name in ({ingredients_list})"
    count_ingredient_ids = f"select count(ingredient_id) from ingredients where ingredient_name in ({ingredients_list})"

    r_result = food_cursor.execute(count_ingredient_ids)
    print('ingredient_id', r_result.fetchall())
    find_recipe_ids_1 = f'select recipe_id from serve where meal_id in(\n' \
                        f'{find_meal_ids})'
    find_recipe_ids_2 = f'select recipe_id from quantity \n' \
                        f'where ingredient_id in ({find_ingredient_ids}) \n' \
                        f'group by recipe_id having count(ingredient_id) = ({count_ingredient_ids})'
    # find_recipe_ids = f'select recipe_id from serve where meal_id = 1;'
    print(find_recipe_ids_2)
    s_result = food_cursor.execute(find_recipe_ids_2)
    print(s_result.fetchall())

    find_recipe = f"select recipe_name from recipes\n " \
                  f"where recipe_id in ({find_recipe_ids_1})\n" \
                  f"and recipe_id in ({find_recipe_ids_2})"
    print('find recipe:\n', find_recipe)
    result = food_cursor.execute(find_recipe)
    print(result.fetchall())
    selected_recipes_list = [i[0] for i in result.fetchall()]
    if selected_recipes_list:
        selected_recipes_string = ", ".join(selected_recipes_list)
        print(f'Recipes selected for you: {selected_recipes_string}')
    else:
        print('no such recipes')
else:
    print('recipe input')
    recipe_input(food_cursor, table_data["measures"], table_data['ingredients'])

conn.commit()
conn.close()
