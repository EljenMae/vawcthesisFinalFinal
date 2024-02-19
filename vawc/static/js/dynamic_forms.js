function showToast(type, message) {
    var toastId = type === 'success' ? '#successToast' : '#errorToast';
    var toast = new bootstrap.Toast(document.querySelector(toastId));
    // Update toast message
    var toastBody = toastId + ' .toast-body';
    $(toastBody).text(message);
    // Show toast
    toast.show();
}
document.addEventListener("DOMContentLoaded", function() {
    const addVictimButton = document.getElementById("add-victim-form");
    const deleteVictimButton = document.getElementById("delete-victim-form");
    const victimFormContainer = document.getElementById("victim-form_0"); // Update the target element
    const victimCountInput = document.getElementById("victim_count");

    addVictimButton.addEventListener("click", function() {
        // Disable the button temporarily to prevent multiple clicks
        addVictimButton.disabled = true;

        const count = parseInt(victimCountInput.value);
        if (count >= 7) {
            showToast('error', 'You can only add up to 7 victims.');
            addVictimButton.disabled = false;
            return;
        }

        const clone = victimFormContainer.cloneNode(true);
        clearInputFields(clone); // Clear input fields of the cloned form
        // Update input field names and ids with appropriate indices
        clone.id = `victim-form_${count}`; // Update the ID of the cloned form
        clone.querySelectorAll('input, select').forEach(input => {
            const name = input.getAttribute('name');
            const id = input.getAttribute('id');
            if (name) {
                const newName = name.replace(/_\d+$/, match => `_${count}`);
                input.setAttribute('name', newName);
            }
            if (id) {
                const newId = id.replace(/_\d+$/, match => `_${count}`);
                input.setAttribute('id', newId);
            }
            const label = clone.querySelector(`[for="${id}"]`);
            if (label) {
                label.setAttribute('for', id.replace(/_\d+$/, match => `_${count}`));
            }
        });

        const victimElement = clone.querySelector('#victim_counter')
        const countplusone = count + 1;
        victimElement.innerHTML = "Victim " + countplusone

        victimFormContainer.parentNode.appendChild(clone); // Append the cloned form to the parent
        victimCountInput.value = count + 1;

        // Enable the button after cloning is complete
        addVictimButton.disabled = false;

        // Scroll to the last form in the container
        clone.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });

    deleteVictimButton.addEventListener("click", function() {
        const forms = document.querySelectorAll("[id^='victim-form_']"); // Update the selector
        if (forms.length > 1) {
            forms[forms.length - 1].remove();
            victimCountInput.value = parseInt(victimCountInput.value) - 1;
        } else {
            showToast('error', 'At least one victim form is required.');
        }
    });

    function clearInputFields(form) {
        const inputs = form.querySelectorAll('input[type="text"], input[type="number"]');
        inputs.forEach(input => {
            input.value = ''; // Clear input value
        });
        const selects = form.querySelectorAll('select');
        selects.forEach(select => {
            select.selectedIndex = 0; // Reset select options to default
        });
    }
});

document.addEventListener("DOMContentLoaded", function() {
    const addPerpetratorButton = document.getElementById("add-perpetrator-form");
    const deletePerpetratorButton = document.getElementById("delete-perpetrator-form");
    const perpetratorFormContainer = document.getElementById("perpetrator-form_0");
    const perpetratorCountInput = document.getElementById("perpetrator_count");

    addPerpetratorButton.addEventListener("click", function() {
        addPerpetratorButton.disabled = true;

        const count = parseInt(perpetratorCountInput.value);
        if (count >= 7) {
            showToast('error', 'You can only add up to 7 perpetrators.');
            addPerpetratorButton.disabled = false;
            return;
        }

        const clone = perpetratorFormContainer.cloneNode(true);
        clearInputFields(clone);
        clone.id = `perpetrator-form_${count}`;
        clone.querySelectorAll('input, select').forEach(input => {
            const name = input.getAttribute('name');
            const id = input.getAttribute('id');
            if (name) {
                const newName = name.replace(/_\d+$/, match => `_${count}`);
                input.setAttribute('name', newName);
            }
            if (id) {
                const newId = id.replace(/_\d+$/, match => `_${count}`);
                input.setAttribute('id', newId);
            }
            const label = clone.querySelector(`[for="${id}"]`);
            if (label) {
                label.setAttribute('for', id.replace(/_\d+$/, match => `_${count}`));
            }
        });

        const perpetratorElement = clone.querySelector('#perpetrator_counter')
        const countplusone = count + 1;
        perpetratorElement.innerHTML = "Perpetrator " + countplusone

        perpetratorFormContainer.parentNode.appendChild(clone);
        perpetratorCountInput.value = count + 1;

        addPerpetratorButton.disabled = false;
        clone.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });

    deletePerpetratorButton.addEventListener("click", function() {
        const forms = document.querySelectorAll("[id^='perpetrator-form_']");
        if (forms.length > 1) {
            forms[forms.length - 1].remove();
            perpetratorCountInput.value = parseInt(perpetratorCountInput.value) - 1;
        } else {
            showToast('error', 'At least one perpetrator form is required.');
        }
    });

    function clearInputFields(form) {
        const inputs = form.querySelectorAll('input[type="text"], input[type="number"]');
        inputs.forEach(input => {
            input.value = '';
        });
        const selects = form.querySelectorAll('select');
        selects.forEach(select => {
            select.selectedIndex = 0;
        });
    }

});












