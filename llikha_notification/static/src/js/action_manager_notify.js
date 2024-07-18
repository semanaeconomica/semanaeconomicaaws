


odoo.define('llikha_notification.ActionManager', function (require) {
"use strict";

/**
 * The purpose of this file is to add the support of Odoo actions of type
 * 'ir_actions_account_report_download' to the ActionManager.
 */

var Notification = require('web.Notification'); 


function isJsonable(v) {
    try{
        return JSON.stringify(v) === JSON.stringify(JSON.parse(JSON.stringify(v)));
     } catch(e){
        /*console.error("not a dict",e);*/
        return false;
    }
}

function isDict(v) {
    return !!v && typeof v==='object' && v!==null && !(v instanceof Array) && !(v instanceof Date) && isJsonable(v);
}

var LlikhaNotification = Notification.extend({
    template: "LlikhaNotification",
    xmlDependencies: (Notification.prototype.xmlDependencies || [])
        .concat(['/llikha_notification/static/src/js/notification_button.xml']),

    init: function(parent, params) {
        this._super(parent, params);
        this.eid = params.eventID;
        this.sticky = true;
        this.name_button = params.name_button;

        this.events = _.extend(this.events || {}, {
            'click .link2showed': function() {
                var self = this;
                if ('with_menssage' in params && params.with_menssage== "1"){
                    llikha_act_message({}, {'data':{'display_name': params.model_notify + ',' + this.eid }},0,0);
                }

                this._rpc({
                    model: params.model_notify,
                    method: params.method_notify,
                    args: [params.eventID],
                }).then(function(r) {
                    if ( isDict(r)){                        
                        if ('type' in r){
                            if (params.auto_close == true)                            
                            {
                                self.close();
                            }
                            return self.do_action(r);
                        }
                        else{
                            if (params.auto_close == true)                            
                            {
                                self.close();
                            }                         
                            self.trigger_up('reload');                                
                            return self.do_action(r);
                        }
                    }
                    else
                    {
                        self.trigger_up('reload');                         
                    }

                    });
            },

            'click .link2close': function() {
                this.close();
            },
        });
    },
}); 




var ActionManager = require('web.ActionManager');
var framework = require('web.framework');
var session = require('web.session');
var localtimeout;
var llikha_act_message= function(attrs, record, estado, intentos) {
        
        localtimeout = setTimeout(function() {
            var newestado = estado;
            if (estado == 0 && intentos == 20){
                return;
            }
            if (this.$(".llikha_oe_throbber_message")[0] != undefined && estado == 0)
            {
                newestado = 1;
            }
            else if (this.$(".llikha_oe_throbber_message")[0] == undefined && estado == 1){
                return;
            }          

            $.post("/notification_llikha",
                 { direccion:  record.model + ',' + record.res_id
                 },
                 function(data,status){
                        if (data === null || data === '') {

                        }else{
                                    $(".llikha_oe_throbber_message").html(data);
                        }       
            });


            this.$(".oe_throbber_message").attr("hidden",true);
            
            try {
              llikha_act_message(attrs, record,newestado, intentos+1);
            }
            catch(error) { 
                return;           
            }
        }, 1000);
    };

ActionManager.include({
    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Executes actions of type 'ir_actions_account_report_download'.
     *
     * @private
     * @param {Object} action the description of the action to execute
     * @returns {Promise} resolved when the report has been downloaded ;
     *   rejected if an error occurred during the report generation
     */
    _executeNotifyLlikha: function (action) {
        var self = this;
        
        this.displayNotification({
            type: action.notify.type,
            title: action.notify.title,
            message: action.notify.message,
            sticky: action.notify.sticky,
        }); 
        
    },
    _executeNotifyButtonLlikha: function (action) {
        var self = this;
        

        this.displayNotification({
                    Notification: LlikhaNotification,
                    title: action.notif_button.title,
                    message: action.notif_button.message,
                    eventID: action.notif_button.eventID,
                    model_notify: action.notif_button.model_notify,
                    method_notify: action.notif_button.method_notify,
                    with_menssage: action.notif_button.with_menssage,
                    name_button: action.notif_button.name_button,
                    auto_close: action.notif_button.auto_close,
                }); 
        
    },




    /**
     * Overrides to handle the 'ir_actions_account_report_download' actions.
     *
     * @override
     * @private clearTimeout(localtimeout);
     */
    _handleAction: function (action, options) {
        clearTimeout(localtimeout); 
        if ('notify' in action) {
            this._executeNotifyLlikha(action, options);
        }
        if ('notif_button' in action) {
            this._executeNotifyButtonLlikha(action, options);
        }
        return this._super.apply(this, arguments);
    },
});


var BasicController = require('web.BasicController')

BasicController.include({

     _callButtonAction: function (attrs, record) {
        if ('o'+'n'+'l'+'y'+'R'+'e'+'a'+'d' in attrs){
            llikha_act_message(attrs, record,0,0);
        }
        return this._super.apply(this, arguments);
    },  


});



});








