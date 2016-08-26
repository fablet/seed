/*
 * :copyright (c) 2014 - 2016, The Regents of the University of California, through Lawrence Berkeley National Laboratory (subject to receipt of any required approvals from the U.S. Department of Energy) and contributors. All rights reserved.
 * :author
 */

angular.module('BE.seed.controller.cycle_admin', [])
.controller('cycle_admin_controller', [
    '$scope',
    '$log',
    'urls',
    'simple_modal_service',
    'Notification',
    'cycle_service',
    'cycles_payload',
    'organization_payload',
    'auth_payload',
function ($scope, $log, urls, simple_modal_service, notification, cycle_service, cycles_payload, organization_payload, auth_payload) {

    $scope.org = organization_payload.organization;
    $scope.auth = auth_payload.auth;
    $scope.cycles = cycles_payload.cycles;

    function initialize_new_cycle() {
        $scope.new_cycle = { from_date:'', to_date:'', name:'' };
    }

    /* UI HANDLERS */
    /* ~~~~~~~~~~~ */
    /* Flag for selected date picker */
    $scope.selectedDatePicker = null;

    // Unfortunately we need to use four flags, one for each picker,
    // rather than an expression in the directive's "is-open" property,
    // since in the latter case the directive will complain
    // that expression is non-assignable.
    $scope.showCreateFromDatePicker = false;
    $scope.showCreateToDatePicker = false;
    $scope.showEditFromDatePicker = false;
    $scope.showEditToDatePicker = false;

    // These scope variables store DatePicker selections
    $scope.createFromDate = ""
    $scope.createToDate = ""
    $scope.editFromDate = ""
    $scope.editToDate = ""

    // Handle datepicker open/close events
    $scope.openDatePicker = function (datePickerFlag) {
      $scope[datePickerFlag] = true;
    };

    /*  Take user input from New Cycle form and submit
        to service to create a new cycle. */
    $scope.submitNewCycleForm = function (form){
        if (form.$invalid) {
            return;
        }
        cycle_service.create_cycle($scope.new_cycle).then(
            function(result){
                get_cycles();
                var msg = 'Created new Cycle ' + getTruncatedName($scope.new_cycle.name);
                notification.primary(msg);
                initialize_new_cycle();
                form.$setPristine();
            },
            function(message){
                $log.error('Error creating new cycle.', message);
            }
        );
    };


    $scope.$watch('createFromDate', function(newval, oldval){
      $scope.checkInvalidCreateDates();
    });

    $scope.$watch('createToDate', function(newval, oldval){
      $scope.checkInvalidCreateDates();
    });

    $scope.checkInvalidCreateDates = function() {
       $scope.invalidCreateDates = ($scope.createToDate < $scope.createFromDate);
    };


    /* Checks for existing cycle name for inline edit form.
        Form assumes function will return a string if there's an existing cycle */
    $scope.checkEditCycleBeforeSave = function(data, currentCycleName){
        if (data === currentCycleName){
            return;
        }
        if (data===undefined || data==='') {
            return 'Enter at least one character';
        }
        if(isCycleNameUsed(data)){
            return 'That Cycle name already exists';
        }
    };

    function isCycleNameUsed(newCycleName) {
				return _.some($scope.cycles, function(obj){
						return obj.name === newCycleName;
				});
    }

    /* Submit edit when 'enter' is pressed */
    $scope.onEditCycleNameKeypress = function(e, form) {
        if (e.which === 13) {
            form.$submit();
        }
    };


    $scope.saveCycle = function(cycle, id, index) {
        //Don't update $scope.cycle until a 'success' from server
        angular.extend(cycle, {id: id});
        cycle_service.update_cycle(cycle).then(
            function(data){
                var msg = 'Cycle updated.';
                notification.primary(msg);
                $scope.cycles.splice(index, 1, data);
                $scope.cycle = data;
            },
            function(message){
                $log.error('Error saving cycle.', message);
            }
        );
    };

		/* A delete operation has lots of consequences that are not completely
		   defined. Not implementing at the moment. */


   function get_cycles(cycle) {
        // gets all cycles for an org user
        cycle_service.get_cycles().then(function(data) {
            // resolve promise
            $scope.cycles = data.cycles;
        });
    }

    function getTruncatedName(name) {
        if (name && name.length>20){
             name = name.substr(0, 20) + '...';
        }
        return name;
    }

    function init(){
       initialize_new_cycle();
    }
    init();

}
]);
