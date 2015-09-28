import json
import random
import gspread
from oauth2client.client import SignedJwtAssertionCredentials


class Chef(object):

  def __init__(self):
    drive_api = self._login()
    # The spreadsheet containing the meal plan
    self._spreadsheet = drive_api.open('Meals')
    # The worksheet with the updated contents of the fridge
    self._fridge_ingredients = self.get_ingredients(
        self._spreadsheet.worksheet('Fridge'))
    # The worksheet where to write the meal plan
    self._output_worksheet = self._spreadsheet.worksheet('Plan')

  def _login(self):
    """Request access to Google Sheets."""
    json_key = json.load(open('credentials.json'))
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = SignedJwtAssertionCredentials(
        json_key['client_email'],
        json_key['private_key'],
        scope)
    return gspread.authorize(credentials)

  def get_ingredients(self, worksheet):
    """Returns the (normalized) ingredients and quantities for a recipe.

    Arguments:
      worksheet: a recipe worksheet, or the fridge worksheet.

    Returns a list of ingredients, their quantities, and units."""
    ingredients_plus_header = worksheet.get_all_values()
    ingredients = ingredients_plus_header[1:]
    return [ [i.lower() for i in cells]
        for cells in ingredients]

  def get_recipe_ingredients(self, title):
    """Helper function to get the ingredients of a recipe, given its name.

    Arguments:
      title: a recipe title

    Returns a list of ingredients, their quantities, and units."""
    worksheet = self._spreadsheet.worksheet(title)
    return self.get_ingredients(worksheet)

  def get_all_recipe_worksheets(self):
    """Returns all the worksheets containing recipes."""
    worksheets = self._spreadsheet.worksheets()
    recipe_worksheets = [w for w in worksheets
        if 'recipe' in w.title.lower()]
    return recipe_worksheets

  def get_ingredient_names(self, ingredients):
    """Returns the name of the ingredients.

    Arguments:
      ingredient: a list of ingredients and their quantities."""
    return set([i[0] for i in ingredients])

  def count_ingredients_already_in_fridge(self, recipe_title):
    """Given a recipe title, returns how many ingredients we already have."""
    ingredients = self.get_ingredient_names(
        self.get_recipe_ingredients(recipe_title))
    fridge_ingredients = self.get_ingredient_names(self._fridge_ingredients)
    already_in_fridge = ingredients.intersection(fridge_ingredients)
    return len(already_in_fridge)

  def get_ingredients_to_buy(self, recipe_title):
    """Given a recipe title, returns the ingredients to buy."""
    ingredients = self.get_recipe_ingredients(recipe_title)
    ingredients_names = self.get_ingredient_names(ingredients)
    fridge_ingredients = self.get_ingredient_names(self._fridge_ingredients)
    to_buy = ingredients_names.difference(fridge_ingredients)
    return ['{}, {} {}'.format(*i) for i in ingredients if i[0] in to_buy]


  def pick_recipes_that_match_the_fridge_content(self, meals=1):
    """Returns a list or recipes chosen at random, giving preferences to the
    ones for which we already have ingredients."""
    population = []
    for recipe_worksheet in self.get_all_recipe_worksheets():
      title = recipe_worksheet.title
      score =  1 + self.count_ingredients_already_in_fridge(title) ** 2
      for _ in range(score):
        population.append(title)
    return set(random.sample(population, meals))

  def write(self, row, column, data):
    """Output to the spreadsheet."""
    self._output_worksheet.update_cell(row, column, data)

  def prepare_meal_plan(self, meals=1):
    """Generates a meal plan, saving it to the spreadsheet."""
    self.write(1, 1, 'Recipes')
    self.write(1, 2, 'Match')
    self.write(1, 3, 'Need to buy')
    for row in range(2, 30):
      for column in range(1, 10):
        self.write(row, column, '')

    selected_recipes = self.pick_recipes_that_match_the_fridge_content(meals=2)
    for index, recipe_title in enumerate(selected_recipes):
      row = index + 2
      self.write(row, 1, recipe_title.replace(' Recipe', ''))
      self.write(row, 2, chef.count_ingredients_already_in_fridge(recipe_title))
      ingredients_to_buy = self.get_ingredients_to_buy(recipe_title)
      for ingredient_index, ingredient in enumerate(ingredients_to_buy):
        self.write(row, 3 + ingredient_index, ingredient)


if __name__ == '__main__':
  chef = Chef()
  chef.prepare_meal_plan(meals=5)
