// http://www.w3schools.com/js/tryit.asp?filename=tryjs_create_object2

function person(firstname, lastname, age, eyecolor)
{
    this.firstname = firstname;
    this.lastname = lastname;
    this.age = age;
    this.eyecolor = eyecolor;
}

var myFather = new person("John", "Doe", 50, "blue");
var myMother = new person("Sally", "Rally", 48, "green");

var elem = document.getElementById("demo");
elem.innerHTML = "My father is " + myFather.age + ". My mother is " + myMother.age;