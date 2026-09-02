Component({options:{styleIsolation:"apply-shared"},properties:{title:String,time:String,kcal:Number,items:{type:Array,value:[]}},methods:{add(){this.triggerEvent("add");}}});
