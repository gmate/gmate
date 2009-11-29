#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Created on Apr 17, 2009

@author: Sergey Chikuyonok (http://chikuyonok.ru)
'''
from zencoding.settings import zen_settings
import re


newline = '\n'
"Символ перевода строки"

insertion_point = '|'
"Символ, указывающий, куда нужно поставить курсор"

sub_insertion_point = ''
"Символ, указывающий, куда нужно поставить курсор (для редакторов, которые позволяют указать несколько символов)"

re_tag = re.compile(r'<\/?[\w:\-]+(?:\s+[\w\-:]+(?:\s*=\s*(?:(?:"[^"]*")|(?:\'[^\']*\')|[^>\s]+))?)*\s*(\/?)>$')

def is_allowed_char(ch):
	"""
	Проверяет, является ли символ допустимым в аббревиатуре
	@param ch: Символ, который нужно проверить
	@type ch: str
	@return: bool
	"""
	return ch.isalnum() or ch in "#.>+*:$-_!@"

def make_map(prop):
	"""
	Вспомогательная функция, которая преобразовывает строковое свойство настроек в словарь
	@param prop: Названия ключа в словаре <code>zen_settings['html']</code>
	@type prop: str
	"""
	obj = {}
	for a in zen_settings['html'][prop].split(','):
		obj[a] = True
		
	zen_settings['html'][prop] = obj
	
def get_newline():
	"""
	Возвращает символ перевода строки, используемый в редакторе
	@return: str
	"""
	return newline

def pad_string(text, pad):
	"""
	Отбивает текст отступами
	@param text: Текст, который нужно отбить
	@type text: str
	@param pad: Количество отступов или сам отступ
	@type pad: int, str
	@return: str
	"""
	pad_str = ''
	result = ''
	if (type(pad) is int):
		pad_str = zen_settings['indentation'] * pad
	else:
		pad_str = pad
		
	nl = get_newline()
	lines = text.split(nl)
	result = result + lines[0]
	for line in lines[1:]:
		result += nl + pad_str + line
		
	return result

def is_snippet(abbr, doc_type = 'html'):
	"""
	Проверяет, является ли аббревиатура сниппетом
	@return bool
	"""
	res = zen_settings[doc_type]
	return res.has_key('snippets') and abbr in res['snippets']

def is_ends_with_tag(text):
	"""
	Проверяет, закачивается ли строка полноценным тэгом. В основном 
	используется для проверки принадлежности символа '>' аббревиатуре 
	или тэгу
	@param text: Текст, который нужно проверить
	@type text: str
	@return: bool
	"""
	return re_tag.search(text) != None

def parse_into_tree(abbr, doc_type = 'html'):
	"""
	Преобразует аббревиатуру в дерево элементов
	@param abbr: Аббревиатура
	@type abbr: str
	@param doc_type: Тип документа (xsl, html)
	@type doc_type: str
	@return: Tag
	"""
	root = Tag('', 1, doc_type)
	parent = root
	last = None
	token = re.compile(r'([\+>])?([a-z][a-z0-9:\!\-]*)(#[\w\-\$]+)?((?:\.[\w\-\$]+)*)(?:\*(\d+))?', re.IGNORECASE)
	
	def expando_replace(m):
		ex = m.group(1)
		if 'expandos' in zen_settings[doc_type] and ex in zen_settings[doc_type]['expandos']:
			return zen_settings[doc_type]['expandos'][ex]
		else:
			return ex
		
	# заменяем разворачиваемые элементы
	abbr = re.sub(r'([a-z][a-z0-9]*)\+$', expando_replace, abbr)
	
	def token_expander(operator, tag_name, id_attr, class_name, multiplier):
		multiplier = multiplier and int(multiplier) or 1
		current = is_snippet(tag_name, doc_type) and Snippet(tag_name, multiplier, doc_type) or Tag(tag_name, multiplier, doc_type)
		
		if id_attr:
			current.add_attribute('id', id_attr[1:])
		if class_name:
			current.add_attribute('class', class_name[1:].replace('.', ' '))
			
		# двигаемся вглубь дерева
		if operator == '>' and token_expander.last:
			token_expander.parent = token_expander.last;
			
		token_expander.parent.add_child(current)
		token_expander.last = current;
		return '';
	
	token_expander.parent = root
	token_expander.last = None
	
	
	abbr = re.sub(token, lambda m: token_expander(m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)), abbr)
	# если в abbr пустая строка — значит, вся аббревиатура без проблем 
	# была преобразована в дерево, если нет, то аббревиатура была не валидной
	return not abbr and root or None;

def find_abbr_in_line(line, index = 0):
	"""
	Ищет аббревиатуру в строке и возвращает ее
	@param line: Строка, в которой нужно искать
	@type line: str
	@param index: Позиция каретки в строке
	@type index: int
	@return: str
	"""
	start_index = 0
	cur_index = index - 1
	while cur_index >= 0:
		ch = line[cur_index]
		if not is_allowed_char(ch) or (ch == '>' and is_ends_with_tag(line[0:cur_index + 1])):
			start_index = cur_index + 1
			break
		cur_index = cur_index - 1
		
	return line[start_index:index], start_index

def expand_abbr(abbr, doc_type = 'html'):
	"""
	Разворачивает аббревиатуру
	@param abbr: Аббревиатура
	@type abbr: str
	@return: str
	"""
	tree = parse_into_tree(abbr, doc_type)
	if tree:
		result = tree.to_string(True)
		if result:
			result = re.sub('\|', insertion_point, result, 1)
			return re.sub('\|', sub_insertion_point, result)
		
	return ''

class Tag(object):
	def __init__(self, name, count = 1, doc_type = 'html'):
		"""
		@param name: Имя тэга
		@type name: str
		@param count:  Сколько раз вывести тэг
		@type count: int
		@param doc_type: Тип документа (xsl, html)
		@type doc_type: str
		"""
		name = name.lower()
		self.name = Tag.get_real_name(name, doc_type)
		self.count = count
		self.children = []
		self.attributes = []
		self.__res = zen_settings[doc_type]
		
		if self.__res.has_key('default_attributes'):
			if name in self.__res['default_attributes']:
				def_attrs = self.__res['default_attributes'][name]				if not isinstance(def_attrs, list):
					def_attrs = [def_attrs]
									for attr in def_attrs:
					for k,v in attr.items():						self.add_attribute(k, v)
				
	@staticmethod
	def get_real_name(name, doc_type = 'html'):
		"""
		Возвращает настоящее имя тэга
		@param name: Имя, которое нужно проверить
		@type name: str
		@param doc_type: Тип документа (xsl, html)
		@type doc_type: str
		@return: str 
		"""
		real_name = name
		if zen_settings[doc_type].has_key('aliases'):
			aliases = zen_settings[doc_type]['aliases']						if name in aliases: # аббревиатура: bq -> blockquote				real_name = aliases[name]			elif ':' in name:				# проверим, есть ли группирующий селектор				group_name = name.split(':', 1)[0] + ':*'				if group_name in aliases:					real_name = aliases[group_name]
		
		return real_name
			
	def add_attribute(self, name, value):
		"""
		Добавляет атрибут
		@param name: Название атрибута
		@type name: str
		@param value: Значение атрибута
		@type value: str
		"""
		self.attributes.append({'name': name, 'value': value})
		
	def add_child(self, tag):
		"""
		Добавляет нового потомка
		@param tag: Потомок
		@type tag: Tag
		"""
		self.children.append(tag)
	
	def __has_element(self, collection_name, def_value = False):
		if collection_name in self.__res:
			return self.name in self.__res[collection_name]
		else:
			return def_value
		
	
	def is_empty(self):
		"""
		Проверяет, является ли текущий элемент пустым
		@return: bool
		"""
		return self.__has_element('empty_elements')
	
	def is_inline(self):
		"""
		Проверяет, является ли текущий элемент строчным
		@return: bool
		"""
		return self.__has_element('inline_elements')
	
	def is_block(self):
		"""
		Проверяет, является ли текущий элемент блочным
		@return: bool
		"""
		return self.__has_element('block_elements', True)
	
	def has_block_children(self):
		"""
		Проверяет, есть ли блочные потомки у текущего тэга. 
		Используется для форматирования
		@return: bool
		"""
		for tag in self.children:
			if tag.is_block():
				return True
		return False
	
	def output_children(self, format = False):
		"""
		Выводит всех потомков в виде строки
		@param format: Нужно ли форматировать вывод
		@return: str
		"""
		content = ''
		for tag in self.children:
				content += tag.to_string(format, True)
				if format and tag.is_block() and self.children.index(tag) != len(self.children) - 1:
					content += get_newline()
		return content
		
	
	def to_string(self, format = False, indent = False):
		"""
		Преобразует тэг в строку. Если будет передан аргумент 
		<code>format</code> — вывод будет отформатирован согласно настройкам
		в <code>zen_settings</code>. Также в этом случае будет ставится 
		символ «|», означающий место вставки курсора. Курсор будет ставится
		в пустых атрибутах и элементах без потомков
		@param format: Форматировать вывод
		@type format: bool
		@param indent: Добавлять отступ
		@type indent: bool
		@return: str
		"""
		cursor = format and '|' or ''
		content = ''
		start_tag = ''
		end_tag = ''
		
		# делаем строку атрибутов
		attrs = ''.join([' %s="%s"' % (p['name'], p['value'] and p['value'] or cursor) for p in self.attributes])
		
		# выводим потомков
		if not self.is_empty():
			content = self.output_children(format)
			
		if self.name:
			if self.is_empty():
				start_tag = '<%s />' % (self.name + attrs,)
			else:
				start_tag, end_tag = '<%s>' % (self.name + attrs,), '</%s>' % self.name
				
		# форматируем вывод
		if format:
			if self.name and self.has_block_children():
				start_tag += get_newline() + zen_settings['indentation']
				end_tag = get_newline() + end_tag;
			
			if content:
				content = pad_string(content, indent and 1 or 0)
			else:
				start_tag += cursor
		
		glue = ''
		if format and self.is_block():
			glue = get_newline()
		
		result = [start_tag.replace('$', str(i + 1)) + content + end_tag for i in range(self.count)]
		return glue.join(result)
	
class Snippet(Tag):
	def __init__(self, name, count = 1, doc_type = 'html'):
		self.name = name
		self.count = count
		self.children = []
		self.__res = zen_settings[doc_type]
		
	def add_attribute(self, name = '', value = ''):
		pass
	
	def is_block(self):
		return True
	
	def to_string(self, format = False, indent = False):
		data = self.__res['snippets'][self.name]
		begin = ''
		end = ''
		content = ''
		child_padding = ''
		child_token = '${child}'
		child_indent = re.compile(r'(^\s+)')
		
		if data:
			if format:
				data = data.replace(r'\n', get_newline())
				# нужно узнать, какой отступ должен быть у потомков
				for line in data.split(get_newline()):
					if child_token in line:
						m = child_indent.match(line)
						child_padding = m and m.group(1) or ''
						break
			
			if child_token in data:
				begin, end = data.split(child_token, 1)
			else:
				begin = data
				
			content = self.output_children(format)
			
			if child_padding:
				content = pad_string(content, child_padding)
		
		glue = format and get_newline() or ''	
		return glue.join([begin.replace(r'\$', str(i + 1)) + content + end for i in range(self.count)])
	
		
make_map('block_elements')
make_map('inline_elements')
make_map('empty_elements')

			
if __name__ == '__main__':
	print(parse_into_tree('ul+').to_string(True))
	print(parse_into_tree('span+em').to_string(True))
	print(parse_into_tree('tmatch', 'xml').to_string(True))
	print(parse_into_tree('d', 'css').to_string(True))
	print(parse_into_tree('cc:ie6>p+blockquote#sample$.so.many.classes*2').to_string(True))

