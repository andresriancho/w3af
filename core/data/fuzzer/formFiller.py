# -*- coding: utf8 -*-
'''
formFiller.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

'''

import core.controllers.outputManager as om


parameter_name_knowledge = {
    'John8212': ['username','user','usuario','benutzername','benutzer'],
    'John': ['name','nombre','nome','name'],  
    'Smith': ['lastname','surname','apellido','sobrenome','vorname','nachname'], 
    'w3af-FrAmEW0rK.': ['pass','word','pswd','pwd','auth','password','passwort','contraseña','senha'], 
    'w3af@email.com':['mail','email','e-mail','correo','correio'], 
    'AK':['state','estado'], 
    'Argentina':['location','country','pais','país','land'], 
    'Buenos Aires':['city','ciudad','cidade','stadt'], 
    'Bonsai Street 123':['addr','address','residence','dirección','direccion','residencia','endereço','endereco','residência','addresse','wohnsitz','wohnort'],
    'Bonsai':['company','empresa','companhia','unternehmen'],  
    'Manager':['position','jon','cargo','posição','unternehmung','position'],
    '90210':['postal','zip','postleitzahl','plz','postais'],
    '3419':['pin','id'],
    '22':['floor','age','piso','edad','stock','alter'],
    '55550178':['phone','code','number','telefono','numero','número','código','codigo','telefon','tel','code','nummer'],        
    '7':['month','day','birthday','birthmonth','mes','dia','día','monat','tag','geburts','mês', 'amount', 'cantidad' ], 
    '1982':['year','birthyear','año','ano','jahr'], 
    'HelloWorld':['content','text'], 
    }

def smartFill( variable_name ):
    '''
    This method returns a "smart" option for a variable name inside a form. For example, if the
    variable_name is "username" a smartFill response would be "john1309", not "0800-111-2233".
    This helps A LOT with server side validation.
    
    @return: The "most likely to be validated as a good value" string, OR '5672' if no match is found.
    '''
    variable_name = variable_name.lower()

    possible_results = []

    for filled_value, variable_name_list in parameter_name_knowledge.items():
        
        for variable_name_db in variable_name_list:
            
            #
            #   If the name in the database is eq to the variable name, there is not much thinking
            #   involved. We just return it.
            #
            if variable_name_db == variable_name:
                return filled_value
                
            if variable_name in variable_name_db:
                possible_results.append( (filled_value, len(variable_name)) )
                continue
                
            if variable_name_db in variable_name:
                possible_results.append( (filled_value, len(variable_name_db)) )
                continue
                
    #
    #   We get here when there is not a 100% match and we need to analyze the possible_results
    #
    if possible_results:
        def sortfunc(x_obj, y_obj):
            return cmp(y_obj[1], x_obj[1])
        
        possible_results.sort(sortfunc)
        
        return possible_results[0][0]
        
    else:
        om.out.debug('[smartFill] Failed to find a value for parameter with name "'+variable_name+'".')
        return '5672'
