# Zen Coding for Gedit
#
# Copyright (C) 2010 Franck Marcia
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

'''
Parse a request and return 'lorem ipsum' string accordingly

Command format:

	c[haracters] [case] [number_of_characters]
	a[lphanumeric] [case] [number_of_characters]
	w[ords] [case] [number_of_words]
	s[entences] [case] [number_of_words_1 [number_of_words_2 [...]]]
	l[ist] [case] [number_of_words_1 [number_of_words_2 [...]]]

	where case is { u[pper] | l[ower] | t[itle] | s[entence] }
	and number_of_words is an integer or a multiplication (for example '3*6')
	
	Commands can be shorten by using initials. For example, "wt 9" is equivalent
	to "words title 9".
	
	See examples at the end of this script.

@author Franck Marcia (franck.marcia@gmail.com)
@link http://github.com/fmarcia/zen-coding-gedit
'''

import random

words = [
	'lorem','ipsum','dolor','sit','amet','consectetur','adipisicing','elit',
	'sed','do','eiusmod','tempor','incididunt','ut','labore','et','dolore',
	'magna','aliqua','ut','enim','ad','minim','veniam','quis','nostrud',
	'exercitation','ullamco','laboris','nisi','ut','aliquip','ex','ea',
	'commodo','consequat','duis','aute','irure','dolor','in',
	'reprehenderit','in','voluptate','velit','esse','cillum','dolore','eu',
	'fugiat','nulla','pariatur','excepteur','sint','occaecat','cupidatat',
	'non','proident','sunt','in','culpa','qui','officia','deserunt',
	'mollit','anim','id','est','laborum'
]
words_bound = 68 # number of words minus 1
words_reset = 23 # number of words per excerpt

characters = [
	'a','b','c','d','e','f','g','h','i','j','k','l','m',
	'n','o','p','q','r','s','t','u','v','w','x','y','z'
]
characters_bound = 25

alphanumeric = [
	'a','b','c','d','e','f','g','h','i','j','k','l','m',
	'n','o','p','q','r','s','t','u','v','w','x','y','z',
	'0','1','2','3','4','5','6','7','8','9'
]
alphanumeric_bound = 35

def to_upper(string):
	return string.upper()

def to_lower(string):
	return string.lower()

def to_title(string):
	return string.title()

def to_sentence(string):
	return string.capitalize()

def default_case(method):
	if method in [get_characters, get_alphanumeric, get_words]:
		return to_lower
	elif method in [get_sentences, get_list]:
		return to_sentence

def get_characters(case, params):
	result = ''
	for param in params:
		for char in range(0, param):
			result += characters[random.randint(0, characters_bound)]
	return case(result)

def get_alphanumeric(case, params):
	result = ''
	for param in params:
		for char in range(0, param):
			result += alphanumeric[random.randint(0, alphanumeric_bound)]
	return case(result)

def get_words(case, params):
	result = []
	for size in params:
		start = 0
		while True:
			end = size if start + words_reset > size else start + words_reset
			start_ex = random.randint(0, words_bound - end + start)
			end_ex = start_ex + end - start
			for word in words[start_ex:end_ex]:
				result.append(word)
			if end == size:
				break
			start += words_reset
	return case(' '.join(result))

def get_sentences(case, params):
	result = []
	for nbwords in params:
		result.append(get_words(case, [nbwords]))
	return '. '.join(result) + '.'

def get_list(case, params):
	result = []
	for nbwords in params:
		result.append(get_words(case, [nbwords]))
	return '\n'.join(result)

def lorem_ipsum(command):

	args = command.split(' ')
	if args[0] == '':
		return ''

	method, case, params = None, None, []

	for arg in args:

		arg = arg.lower()
		if arg.isdigit():

			if not method:
				method = get_list

			if not case:
				case = default_case(method)

			params.append(int(arg))

		else:

			test = arg.split('*')
			if len(test) == 2 and test[0].isdigit() and test[1].isdigit():
				if not method:
					method = get_list
				if not case:
					case = default_case(method)
				for x in range(0, int(test[1])):
					params.append(int(test[0]))
				continue

			if len(params) == 0:

				if len(arg) == 1:

					if not method and not case:
						if   arg == 'c': method = get_characters
						elif arg == 'a': method = get_alphanumeric
						elif arg == 'w': method = get_words
						elif arg == 's': method = get_sentences
						elif arg == 'l': method = get_list

					elif not case:
						if   arg == 'l': case = to_lower
						elif arg == 'u': case = to_upper
						elif arg == 't': case = to_title
						elif arg == 's': case = to_sentence
					
				elif len(arg) == 2:
				
					if not method and not case:
						if   arg == 'cu': method = get_characters; case = to_upper
						elif arg == 'cl': method = get_characters; case = to_lower
						elif arg == 'ct': method = get_characters; case = to_title
						elif arg == 'au': method = get_alphanumeric; case = to_upper
						elif arg == 'al': method = get_alphanumeric; case = to_lower
						elif arg == 'at': method = get_alphanumeric; case = to_title
						elif arg == 'wu': method = get_words; case = to_upper
						elif arg == 'wl': method = get_words; case = to_lower
						elif arg == 'wt': method = get_words; case = to_title
						elif arg == 'su': method = get_sentences; case = to_upper
						elif arg == 'sl': method = get_sentences; case = to_lower
						elif arg == 'st': method = get_sentences; case = to_title
						elif arg == 'lu': method = get_list; case = to_upper
						elif arg == 'll': method = get_list; case = to_lower
						elif arg == 'lt': method = get_list; case = to_title

				else:

					if not method and not case:
						if   arg == 'characters': method = get_characters
						elif arg == 'alphanumeric': method = get_alphanumeric
						elif arg == 'words': method = get_words
						elif arg == 'sentences': method = get_sentences
						elif arg == 'list': method = get_list

					elif not case:
						if   arg == 'lower': case = to_lower
						elif arg == 'upper': case = to_upper
						elif arg == 'title': case = to_title
						elif arg == 'sentence': case = to_sentence

	if len(params) == 0:
		params = [1]

	if method is None:
		method = get_list
		
	if case is None:
		case = default_case(method)

	return method(case, params)

if __name__ == '__main__':
	def echo(x):
		print x + ':', '(' + lorem_ipsum(x) + ')'
	echo('')
	echo('characters')
	echo('characters 10')
	echo('characters upper 10')
	echo('characters lower 10')
	echo('characters title 10')
	echo('characters sentence 10')
	echo('characters 3*2')
	echo('characters upper 3*2')
	echo('alphanumeric')
	echo('alphanumeric 10')
	echo('alphanumeric upper 10')
	echo('alphanumeric lower 10')
	echo('alphanumeric title 10')
	echo('alphanumeric sentence 10')
	echo('alphanumeric 3*2')
	echo('alphanumeric upper 3*2')
	echo('words')
	echo('words 3')
	echo('words upper 3')
	echo('words lower 3')
	echo('words title 3')
	echo('words sentence 3')
	echo('words 3*2')
	echo('words upper 3*2')
	echo('sentences')
	echo('sentences 3 2')
	echo('sentences upper 3 2')
	echo('sentences lower 3 2')
	echo('sentences title 3 2')
	echo('sentences sentence 3 2')
	echo('sentences 3*2')
	echo('sentences upper 3*2')
	echo('list')
	echo('list 3')
	echo('list 3 2')
	echo('list upper 3 2')
	echo('list lower 3 2')
	echo('list title 3 2')
	echo('list sentence 3 2')
	echo('list 3*2')
	echo('list upper 3*2')
	echo('c 10')
	echo('c u 10')
	echo('a 10')
	echo('a t 10')
	echo('w 7')
	echo('w l 7')
	echo('s 5 3 9')
	echo('s t 7 4 6')
	echo('l 4 7')
	echo('l u 3 2 6')
	echo('cu 10')
	echo('au 10')
	echo('wl 7')
	echo('st 7 4 6')
	echo('lu 3 2 6')
	echo('l 7*5')

