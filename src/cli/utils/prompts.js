/**
 * CLI Prompts
 */

import inquirer from 'inquirer';

/**
 * Prompt for confirmation
 */
export async function promptConfirm(message, defaultValue = false) {
  const { confirmed } = await inquirer.prompt([{
    type: 'confirm',
    name: 'confirmed',
    message,
    default: defaultValue
  }]);
  return confirmed;
}

/**
 * Prompt for text input
 */
export async function promptInput(message, defaultValue = '') {
  const { value } = await inquirer.prompt([{
    type: 'input',
    name: 'value',
    message,
    default: defaultValue
  }]);
  return value;
}

/**
 * Prompt for password input
 */
export async function promptPassword(message) {
  const { value } = await inquirer.prompt([{
    type: 'password',
    name: 'value',
    message,
    mask: '*'
  }]);
  return value;
}

/**
 * Prompt for selection from list
 */
export async function promptSelect(message, choices) {
  const { value } = await inquirer.prompt([{
    type: 'list',
    name: 'value',
    message,
    choices
  }]);
  return value;
}

/**
 * Prompt for multiple selection
 */
export async function promptMultiSelect(message, choices) {
  const { values } = await inquirer.prompt([{
    type: 'checkbox',
    name: 'values',
    message,
    choices
  }]);
  return values;
}

/**
 * Prompt for number input
 */
export async function promptNumber(message, defaultValue = 0) {
  const { value } = await inquirer.prompt([{
    type: 'number',
    name: 'value',
    message,
    default: defaultValue
  }]);
  return value;
}

/**
 * Prompt for path input with autocomplete
 */
export async function promptPath(message, defaultValue = '') {
  const { value } = await inquirer.prompt([{
    type: 'input',
    name: 'value',
    message,
    default: defaultValue
  }]);
  return value;
}
