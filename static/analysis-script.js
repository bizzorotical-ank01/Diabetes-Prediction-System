$(document).ready(() => {
    $('#div_data_table').hide();
    $('#div_clean_data_table').hide();
    $('#div_train_data_table').hide();
    $('#div_test_data_table').hide();

    $('#btn-clean-data').removeClass('d-flex');
    $('#btn-clean-data').css('display', 'none');
    $('#btn-train-model').removeClass('d-flex');
    $('#btn-train-model').css('display', 'none');
});

$("#load_data").on('change', function () {
    console.log($('#load_data').prop('files')[0])
    const csvFile = $('#load_data').prop('files')[0];
    const reader = new FileReader();

    reader.onload = (event) => {
        const text = event.target.result;
        const [headers, data] = ObjectifyCSV(text);

        // Hide the input card and show tablular_view on successful upload
        $('#input_card').hide();
        $('#btn-clean-data').addClass('d-flex');
        $('#div_data_table').show();

        fillDataInTable(headers, data, '#data_table'); // arguments => headers, data, tableId
    }

    reader.readAsText(csvFile);
});


function ObjectifyCSV(str, delimiter = ",") {
    // slice from start of text to the first \n index
    // use split to create an array from string by delimiter
    let headers = str.slice(0, str.indexOf("\n")).split(delimiter).map(
        (value) => { return value.replace("\r", ""); }
    );

    // slice from \n index + 1 to the end of the text
    // use split to create an array of each csv value row
    let rows = str.slice(str.indexOf("\n") + 1).split("\n").map(
        (value) => { return value.replace("\r", ""); }
    );

    // Map the rows
    // split values from each row into an array
    // use headers.reduce to create an object
    // object properties derived from headers:values
    // the object passed as an element of the array
    const arr = rows.map(function (row) {
        const values = row.split(delimiter);
        const el = headers.reduce(function (object, header, index) {
            object[header] = values[index];
            return object;
        }, {});
        return el;
    });

    localStorage.setItem('objectified_data', JSON.stringify(arr));
    return [headers, arr]

}

function fillDataInTable(headers, data, tableId) {
    let [tableStructure, tableHead, tableData] = ['', '', ''];
    let table = $(tableId);
    console.log(headers)

    headers.forEach((header) => tableHead += `<th scope="col">${header}</th>`);
    data.forEach((row, index) => {
        let rowDetails = `<tr> <th scope="row">${index}</th>`;
        let rowValues = Object.values(row);
        rowValues.forEach((cellValue) => rowDetails += `<td> ${cellValue} </td>`);
        rowDetails += '</tr>';

        tableData += rowDetails;
    });

    tableStructure += `
        <thead class="thead-dark">
            <tr> 
                <th scope="col">#</th>
                ${tableHead} 
            </tr>
        </thead>

        <tbody>
            ${tableData}
        </tbody>
    `
    table.append(tableStructure);
    table.DataTable();
}

function cleanData() {
    const data = localStorage.objectified_data;

    $.ajax({
        url: '/clean_data',
        type: 'POST',
        data: data,   // converts js value to JSON string
        contentType: 'application/json;charset=UTF-8',
    }).done(function (response) {     // on success get the return object from server
        if (response.status == 200) {
            const headers = response.data.headers;

            fillDataInTable(headers, response.data.clean_data, '#clean_data_table');
            fillDataInTable(headers, response.data.train_data, '#train_data_table');
            fillDataInTable(headers, response.data.test_data, '#test_data_table');

            $('#div_data_table').remove();

            $('#div_clean_data_table').show();
            $('#div_train_data_table').show();
            $('#div_test_data_table').show();
            $('#btn-clean-data').removeClass('d-flex');
            $('#btn-clean-data').css('display', 'none');
            $('#btn-train-model').addClass('d-flex');

            localStorage.setItem('clean_objectified_data', JSON.stringify(response.data))
        }
    })
}

function trainModel() {

    $.ajax({
        url: '/train_model',
        type: 'POST',
        data: localStorage.clean_objectified_data,   // converts js value to JSON string
        contentType: 'application/json;charset=UTF-8',
    }).done(function (response) {     // on success get the return object from server
        if (response.status == 200) {
            console.log("Trained the model");
            $('#modal-title').append(`${response.message}`);
            $('#modal-body').append(`<p> ${response.body} </p>`);
            $('#modal').modal({backdrop: 'static', keyboard: false});  
        }
        else {
            $('#mdoal-title').append(`${response.message}`);
            $('#modal-body').append('<p> SOMETING WENT WRONG </p>');
            $('#modal').modal({backdrop: 'static', keyboard: false});
        }
    });
}