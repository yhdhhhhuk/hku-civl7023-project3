// P3-GrooveKey-v2; mm; origin = bottom plane centre.
// Dimensional reference is parameters.json; total envelope 50 x 30 x 25.
module rect_loft(cx,z,h,bottom,top) {
  bx=bottom[0]/2; by=bottom[1]/2; tx=top[0]/2; ty=top[1]/2;
  polyhedron(points=[[cx-bx,-by,z],[cx+bx,-by,z],[cx+bx,by,z],[cx-bx,by,z],
                     [cx-tx,-ty,z+h],[cx+tx,-ty,z+h],[cx+tx,ty,z+h],[cx-tx,ty,z+h]],
             faces=[[3,2,1,0],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]);
}
union() {
  difference() {
    translate([-25,-15,0]) cube([50,30,22]);
    for (y=[-15,11]) translate([-19,y,10]) cube([38,4,12.01]);
    for (x=[-20,20]) {
      rect_loft(x,-0.001,0.501,[8.004,12.004],[6,10]);
      translate([x-3,-5,0.499]) cube([6,10,3.002]);
    }
  }
  for (x=[-20,20]) rect_loft(x,22,3,[4,8],[2,6]);
}
