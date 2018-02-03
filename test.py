from src.slide import Slide
# import sys
# print "%03d" % 3
# sys.exit(0)

data = {
	"slideType":"sectionHeader",
	"transitionIn":"immediate",
	"duration":7000,
	"transitionOut":"fadeOutOverNext",
	"transitionOutDuration":1000,
	"layers":[
		{
		  "resourceType":"graphic",
		  "resourceUrl":"https://s3.amazonaws.com/dev.wom.com/flower_right.png",
		  "transitionIn":"bloom",
		  "transitionInDuration":3000,
		  "transitionInStart":0,
		  "transitionOut":"fadeOut",
		  "transitionOutDuration":300,
		  "transitionOutStart":6700,
		  "topStart":"40%",
          "leftStart":"103%",
		  "top": "33%",
		  "left":"100%",
		  "width":"30%",
		  "height":"30%"
		},
		{
		  "resourceType":"graphic",
		  "resourceUrl":"https://s3.amazonaws.com/dev.wom.com/flower_left.png",
		  "transitionIn":"bloom",
		  "transitionInDuration":3000,
		  "transitionInStart":0,
		  "transitionOut":"fadeOut",
		  "transitionOutDuration":300,
		  "transitionOutStart":6700,
		  "topStart":"35%",
          "leftStart":"-8%",
		  "top": "30%",
		  "left":"0%",
		  "width":"23%",
		  "height":"23%"
		},
		{
		  "resourceType":"graphic",
		  "resourceUrl":"https://s3.amazonaws.com/dev.wom.com/flower_bottom.png",
		  "transitionIn":"bloom",
		  "transitionInDuration":3000,
		  "transitionInStart":0,
		  "transitionOut":"fadeOut",
		  "transitionOutDuration":300,
		  "transitionOutStart":6700,
		  "topStart":"112%",
          "leftStart":"50%",
		  "top": "102%",
		  "left":"50%",
		  "width":"44%",
		  "height":"44%"
		},
		{
		  "resourceType":"text",
		  "resourceUrl":"https://fonts.googleapis.com/css?family=Dancing+Script",
		  "fontFamily":"Danicng Script",
		  "fontSize":"100px",
		  "kerning":0,
		  "color":"#01BFD7",
		  "text":"Miriam Kramer",
		  "transitionIn":"wipeLeftToRight",
		  "transitionInStart":1000,
		  "transitionInDuration":2000,
		  "transitionOut":"fadeOut",
		  "transitionOutDuration":300,
		  "transitionOutStart":6700
		},
		{
		  "resourceType":"text",
		  "resourceUrl":"https://fonts.googleapis.com/css?family=Arbutus+Slab",
		  "fontFamily":"Arbutus Slab",
		  "fontSize":"15px",
		  "kerning":10,
		  "color":"#7c7c7c",
		  "text":"WE REMEMBER",
		  "transitionIn":"fadeIn",
		  "transitionInStart":1000,
		  "transitionInDuration":2000,
		  "top":"35%",
		  "transitionOut":"fadeOut",
		  "transitionOutDuration":300,
		  "transitionOutStart":6700
		},
		{
		  "resourceType":"text",
		  "resourceUrl":"https://fonts.googleapis.com/css?family=Arbutus+Slab",
		  "fontFamily":"Arbutus Slab",
		  "fontSize":"15px",
		  "kerning": 10,
		  "color":"#7c7c7c",
		  "text":"APRIL 13, 1928 - SEPT. 24, 2011",
		  "transitionIn":"fadeIn",
		  "transitionInStart":1000,
		  "transitionInDuration":2000,
		  "top":"65%",
		  "transitionOut":"fadeOut",
		  "transitionOutDuration":300,
		  "transitionOutStart":6700
		}
	]
}
s = Slide(data)
s.render()