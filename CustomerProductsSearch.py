# -*- coding: iso-8859-1 -*-

# Written by Enrico


import sublime
import sublime_plugin
import sys
import json
import os
import copy


SEARCHFILE = sublime.packages_path()+os.path.sep+"CustomerProductSearch"+os.path.sep+"customer_product_search.tmp"
CUSTOMER_PRODUCT_HASH_FILE = os.path.sep+"db"+os.path.sep+"customer_product_hash.json"

class CustomerProductSearchCommand(sublime_plugin.WindowCommand):

    active_view = ""
    data_map = ""
    customer_products = {}
    user_with_not_products_array = []

    def run(self):
        #oeffne suchfile in neuem View
        self.active_view = self.window.open_file(SEARCHFILE)
        #begin editieren, viewinhalt wird geloescht, edit_obj wird zurueckgeliefert
        self.clear_view()
        try:
            customer_product_hash_file = ""
            #suche die json Datei
            for folder in self.window.folders():
                if os.path.exists(folder+CUSTOMER_PRODUCT_HASH_FILE):
                    customer_product_hash_file = folder+CUSTOMER_PRODUCT_HASH_FILE
            f = open(customer_product_hash_file)
            #json laden
            self.data_map = json.load(f)
            f.close()
            self.save_view()
            #tabname
            self.active_view.set_name("customer_product_search.tmp")
            self.active_view.window().focus_view(self.active_view)
            #sucheingabe einblenden
            self.active_view.window().show_input_panel('Search Product', '', self.on_done, self.on_change, self.on_cancel)
        except:
            #fehler beim oeffnen der json Datei
            self.insert_text(u'Fehler beim oeffnen, der "db/customer_product_hash.json",\nSelfcare Rake Task "rake db:import:build_customer_products_hash" benutzen um eine neue Datei zu erzeugen.', False)

    def show_results(self, results):
        self.clear_view()
        #enumerate liefert ein counter
        for (counter, result) in enumerate(results):
          #ergebnis anzeige
          self.insert_text("n"+result[0]+"@wsct.eu | Treffer:"+str(result[1])+"("+self.customer_products[result[0]]+")\n",True)
        self.save_view()

    def insert_text(self, txt, append):
        edit = self.active_view.begin_edit()
        if not append:
            self.active_view.erase(edit, sublime.Region(0, self.active_view.size()))
        self.active_view.insert(edit, self.active_view.size(), txt)
        self.active_view.end_edit(edit)

    def clear_view(self):
        edit = self.active_view.begin_edit()
        self.active_view.erase(edit, sublime.Region(0, self.active_view.size()))
        self.active_view.end_edit(edit)

    def save_view(self):
       if (self.active_view.file_name() and self.active_view.is_dirty() and os.path.exists(self.active_view.file_name())):
           self.active_view.run_command('save')

    def search(self, dictionary, substr, user_with_not_products_array):
        result = {}
        for key , value in dictionary.iteritems():
            if substr in key:
                for i in user_with_not_products_array:
                    if i in value:
                        value.remove(i)
                if value:
                    result [key] = value
        return result

    def get_input_values(self, search_string_array):
        not_products_array = []
        next_value_is_not_product = False
        for (counter, search_value) in enumerate(search_string_array):
            if not search_value.strip():
                continue
            if next_value_is_not_product is True:
                not_products_array.append(search_value)
            next_value_is_not_product = False
            if search_value == "NOT":
                next_value_is_not_product = True
        for i in not_products_array: search_string_array.remove(i)
        if "NOT" in search_string_array: search_string_array.remove("NOT")
        return  list(search_string_array), not_products_array

    def user_with_not_products(self, not_products_array, dictionary):
        user = []
        for not_product in not_products_array:
            for product , customer_accounts in dictionary.iteritems():
                if not_product in product:
                    user.append(customer_accounts)
        if user != []:
            return reduce(lambda x, y: x+y, user)
        else:
            return []

    def on_change(self, input):
        search_results = []
        self.customer_products = {}
        self.user_with_not_products_array = []
        data_map_copy = copy.deepcopy(self.data_map)
        search_string_array , not_products_array = self.get_input_values(self.get_search_string_array(input))
        self.user_with_not_products_array = self.user_with_not_products(not_products_array, data_map_copy)
        for search_value in search_string_array:
            #wieso auch immer hier manchmal ein "leerzeichen" als value existiert
            if not search_value.strip():
                continue
            for product, customer_accounts in self.search(data_map_copy, search_value, self.user_with_not_products_array).iteritems():
                if customer_accounts:
                    for customer_account in customer_accounts:
                       self.add_customer_result(customer_account, product)
                    search_results.append(customer_accounts)
        self.prepare_results(search_results)

    def get_search_string_array(self, input):
        search_string = str(input)
        if not search_string:
            self.insert_text('', False)
        #eingabe trennen anhand der leerzeichen
        return search_string.upper().split(' ')

    def add_customer_result(self, customer_account, product):
        if self.customer_products.get(customer_account,''):
            if product not in self.customer_products[customer_account].split(','):
                self.customer_products[customer_account] = self.customer_products[customer_account]+","+ product
        else:
            self.customer_products[customer_account] = product

    def prepare_results(self, search_results):
        #reduce(lambda x,y: x+y, [[1],[2],[3],[4]])
        #[1, 2, 3, 4]
        results = {}
        if search_results != []:
            flatten_results = reduce(lambda x, y: x+y, search_results)
            results_dict = {}
            for result in flatten_results:
                results_dict[result] = flatten_results.count(result)
            results = Counter(results_dict).most_common(5)
        self.show_results(results)

    def on_done(self, input):
        #dirty, nach enter wird panel wieder angezeigt
        self.active_view.window().show_input_panel('Search Product', input , self.on_done, self.on_change, self.on_cancel)

    def gotoMarker(self, auswahl):
        pass

    def on_cancel(self):
        pass


from operator import itemgetter
from heapq import nlargest
from itertools import repeat, ifilter

class Counter(dict):
    '''Dict subclass for counting hashable objects.  Sometimes called a bag
    or multiset.  Elements are stored as dictionary keys and their counts
    are stored as dictionary values.

    >>> Counter('zyzygy')
    Counter({'y': 3, 'z': 2, 'g': 1})

    '''

    def __init__(self, iterable=None, **kwds):
        '''Create a new, empty Counter object.  And if given, count elements
        from an input iterable.  Or, initialize the count from another mapping
        of elements to their counts.

        >>> c = Counter()                           # a new, empty counter
        >>> c = Counter('gallahad')                 # a new counter from an iterable
        >>> c = Counter({'a': 4, 'b': 2})           # a new counter from a mapping
        >>> c = Counter(a=4, b=2)                   # a new counter from keyword args

        '''
        self.update(iterable, **kwds)

    def __missing__(self, key):
        return 0

    def most_common(self, n=None):
        '''List the n most common elements and their counts from the most
        common to the least.  If n is None, then list all element counts.

        >>> Counter('abracadabra').most_common(3)
        [('a', 5), ('r', 2), ('b', 2)]

        '''
        if n is None:
            return sorted(self.iteritems(), key=itemgetter(1), reverse=True)
        return nlargest(n, self.iteritems(), key=itemgetter(1))

    def elements(self):
        '''Iterator over elements repeating each as many times as its count.

        >>> c = Counter('ABCABC')
        >>> sorted(c.elements())
        ['A', 'A', 'B', 'B', 'C', 'C']

        If an element's count has been set to zero or is a negative number,
        elements() will ignore it.

        '''
        for elem, count in self.iteritems():
            for _ in repeat(None, count):
                yield elem

    # Override dict methods where the meaning changes for Counter objects.

    @classmethod
    def fromkeys(cls, iterable, v=None):
        raise NotImplementedError(
            'Counter.fromkeys() is undefined.  Use Counter(iterable) instead.')

    def update(self, iterable=None, **kwds):
        '''Like dict.update() but add counts instead of replacing them.

        Source can be an iterable, a dictionary, or another Counter instance.

        >>> c = Counter('which')
        >>> c.update('witch')           # add elements from another iterable
        >>> d = Counter('watch')
        >>> c.update(d)                 # add elements from another counter
        >>> c['h']                      # four 'h' in which, witch, and watch
        4

        '''
        if iterable is not None:
            if hasattr(iterable, 'iteritems'):
                if self:
                    self_get = self.get
                    for elem, count in iterable.iteritems():
                        self[elem] = self_get(elem, 0) + count
                else:
                    dict.update(self, iterable) # fast path when counter is empty
            else:
                self_get = self.get
                for elem in iterable:
                    self[elem] = self_get(elem, 0) + 1
        if kwds:
            self.update(kwds)

    def copy(self):
        'Like dict.copy() but returns a Counter instance instead of a dict.'
        return Counter(self)

    def __delitem__(self, elem):
        'Like dict.__delitem__() but does not raise KeyError for missing values.'
        if elem in self:
            dict.__delitem__(self, elem)

    def __repr__(self):
        if not self:
            return '%s()' % self.__class__.__name__
        items = ', '.join(map('%r: %r'.__mod__, self.most_common()))
        return '%s({%s})' % (self.__class__.__name__, items)

    # Multiset-style mathematical operations discussed in:
    #       Knuth TAOCP Volume II section 4.6.3 exercise 19
    #       and at http://en.wikipedia.org/wiki/Multiset
    #
    # Outputs guaranteed to only include positive counts.
    #
    # To strip negative and zero counts, add-in an empty counter:
    #       c += Counter()

    def __add__(self, other):
        '''Add counts from two counters.

        >>> Counter('abbb') + Counter('bcc')
        Counter({'b': 4, 'c': 2, 'a': 1})


        '''
        if not isinstance(other, Counter):
            return NotImplemented
        result = Counter()
        for elem in set(self) | set(other):
            newcount = self[elem] + other[elem]
            if newcount > 0:
                result[elem] = newcount
        return result

    def __sub__(self, other):
        ''' Subtract count, but keep only results with positive counts.

        >>> Counter('abbbc') - Counter('bccd')
        Counter({'b': 2, 'a': 1})

        '''
        if not isinstance(other, Counter):
            return NotImplemented
        result = Counter()
        for elem in set(self) | set(other):
            newcount = self[elem] - other[elem]
            if newcount > 0:
                result[elem] = newcount
        return result

    def __or__(self, other):
        '''Union is the maximum of value in either of the input counters.

        >>> Counter('abbb') | Counter('bcc')
        Counter({'b': 3, 'c': 2, 'a': 1})

        '''
        if not isinstance(other, Counter):
            return NotImplemented
        _max = max
        result = Counter()
        for elem in set(self) | set(other):
            newcount = _max(self[elem], other[elem])
            if newcount > 0:
                result[elem] = newcount
        return result

    def __and__(self, other):
        ''' Intersection is the minimum of corresponding counts.

        >>> Counter('abbb') & Counter('bcc')
        Counter({'b': 1})

        '''
        if not isinstance(other, Counter):
            return NotImplemented
        _min = min
        result = Counter()
        if len(self) < len(other):
            self, other = other, self
        for elem in ifilter(self.__contains__, other):
            newcount = _min(self[elem], other[elem])
            if newcount > 0:
                result[elem] = newcount
        return result

