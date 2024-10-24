
function displayTheData() {
  $(document).ready(function () {
     $("#printTheDivisionValue").html($("#printThisDivIdOnButtonClick").html());
  });
}
  
const currentDate=new Date()
const currentHour=currentDate.getHours()
const currentMinute = currentDate.getMinutes()
const ls=currentHour+":"+currentMinute
document.getElementById('time').innerHTML=ls;


  function PrintDiv(id) {
    var data=document.getElementById(id).innerHTML;
    var myWindow = window.open('', 'my div', 'height=400,width=600');
    myWindow.document.write('<html><head><title>my div</title>');
    /*optional stylesheet*/ //myWindow.document.write('<link rel="stylesheet" href="main.css" type="text/css" />');
    myWindow.document.write('</head><body >');
    myWindow.document.write(data);
    myWindow.document.write('</body></html>');
    myWindow.document.close(); // necessary for IE >= 10

    myWindow.onload=function(){ // necessary if the div contain images

        myWindow.focus(); // necessary for IE >= 10
        myWindow.print();
        myWindow.close();
    };
}




function printDiv(divName) {
  var printContents = document.getElementById(divName).innerHTML;
  var originalContents = document.body.innerHTML;

  document.body.innerHTML = printContents;

  window.print();

  document.body.innerHTML = originalContents;
}