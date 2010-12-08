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
    'John8212': ['username','user','uname','usuario','benutzername','benutzer', 'nickname', 'logname', 'ident'],
    'John': ['name','nombre','nome','name', 'naam'],  
    'Smith': ['lastname','surname','apellido','sobrenome','vorname','nachname'], 
    
    'FrAmE30.': ['pass','word','pswd','pwd','auth','password','passwort','contraseña','senha',
                                    'key', 'hash', 'pword', 'passe'], 

    'w3af@email.com':['mail','email','e-mail','correo','correio', 'to', 'cc', 'bcc'], 
    'http://w3af.sf.net/':['link', 'enlace', 'target', 'destino', 'website', 'web'], 
    
    'AK':['state','estado'], 
    'Argentina':['location','country','pais','país','land'], 
    'English':['language', 'lang',  'idioma'], 
    'Buenos Aires':['city','ciudad','cidade','stadt'], 
    'Bonsai Street 123':['addr','address','residence','dirección','direccion','residencia',
                                    'endereço','endereco','residência','addresse','wohnsitz','wohnort'],
    
    'Bonsai':['company','empresa','companhia','unternehmen'],  
    'Manager':['position','jon','cargo','posição','unternehmung','position'],
    
    '90210':['postal','zip','postleitzahl','plz','postais'],
    '3419':['pin','id', 'suffix'],
    '22':['floor','age','piso','edad','stock','alter', 'port', 'puerto'],
    '555':['area', 'prefijo','prefix'],
    '55550178':['phone','fax','code','number','telefono','numero','número','código','codigo','telefon',
                        'tel','code','nummer', 'call', 'llamar', 'passport', 'pasaporte'],
    '987654320': ['ssn', 'social'], 
    '7':['month','day','birthday','birthmonth','mes','dia','día','monat','tag','geburts','mês',
            'amount', 'cantidad', 'precio', 'price', 'value', 'type', 'tipo', 'article', 'score', 'puntos', 
            'hour', 'hora', 'minute', 'minuto', 'second', 'segundo', 'weight','peso', 'largo', 'length',
             'height', 'altura', 'step', 'pageid'], 
    '1982':['year','birthyear','año','ano','jahr', 'since', 'desde'], 
    
    'Hello World':['content','text', 'words', 'query', 'search', 'keyword', 'title', 'desc', 'data',
                             'payload', 'answer', 'respuesta', 'description', 'descripcion', 
                             'message', 'mensaje', 'excerpt', 'comment', 'comentario'], 
                             
    'Spam or Eggs?':['question', 'pregunta'], 
    
    '<html>w3af</html>':['html', 'wysiwyg'], 
    
    'Blue':['color'], 
    
    '1':['debug', 'is_admin', 'admin', 'verbose'], 
    
    '127.0.0.1':['ip', 'ipaddress', 'host', 'server', 'servidor'], 
    '255.255.255.0':['netmask', 'mask', 'mascara'], 
    'w3af.sf.net':['domain', 'dominio']
    
    }


def sortfunc(x_obj, y_obj):
    '''
    A simple sort function to sort the values of a list using the second item of each item.
    @return: The answer to: which one is greater?
    '''
    return cmp(y_obj[1], x_obj[1])

def get_match_rate(variable_name, variable_name_db):
    '''
    @parameter variable_name: The name of the variable for which we want a value
    @parameter variable_name_db: A name from the DB that ressembles the variable_name
    
    @return: A match rate between variable_name and variable_name_db.
    '''
    match_rate = len(variable_name)
    if variable_name.startswith(variable_name_db):
        match_rate += len(variable_name) / 2
    return match_rate

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
                match_rate = get_match_rate(variable_name, variable_name_db)
                possible_results.append( (filled_value, match_rate) )
                continue
                
            if variable_name_db in variable_name:
                match_rate = get_match_rate(variable_name, variable_name_db)
                possible_results.append( (filled_value, match_rate) )
                continue
                
    #
    #   We get here when there is not a 100% match and we need to analyze the possible_results
    #
    if possible_results:
        possible_results.sort(sortfunc)
        return possible_results[0][0]
        
    else:
        msg = '[smartFill] Failed to find a value for parameter with name "'
        msg += variable_name + '".'
        om.out.debug( msg )
        
        return '56'
