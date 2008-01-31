function toggleDiv(divid){
	if(document.getElementById(divid).style.display == 'none'){
		document.getElementById(divid).style.display = '';
	}else{
		document.getElementById(divid).style.display = 'none';
	}
}

function paint(divid){
	if ( document.getElementById( divid ).className == "plugNameOn" ) {	
		document.getElementById( divid ).className = "plugName";
	}else{
		document.getElementById( divid ).className = "plugNameOn";
	}
}

function refresh() { window.location.href = self.location.href;}
