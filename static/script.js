
   document.addEventListener('DOMContentLoaded', function () {
    const title = document.getElementById('euft-title');
    if (title) {
        // Fase 1: Título aparece devagar e aumenta de tamanho
        title.classList.add('fade-in-slow');

        // Fase 2: Após o fade-in, ele pisca
        setTimeout(() => {
            title.classList.remove('fade-in-slow');
            title.classList.add('blink');
        }, 2000); // tempo do fade-in

        // Fase 3: Após o piscar, ele se fixa visível
        setTimeout(() => {
            title.classList.remove('blink');
            title.style.opacity = '1';
        }, 4000); // tempo total = fade + blink
    }

    const btnShowResults = document.getElementById('showResults');
    const btnShowErrors = document.getElementById('showErrors');

    if (btnShowResults) {
        btnShowResults.addEventListener('click', function () {
            document.getElementById('results').style.display = 'block';
            document.getElementById('errors').style.display = 'none';
        });
    }

    if (btnShowErrors) {
        btnShowErrors.addEventListener('click', function () {
            document.getElementById('errors').style.display = 'block';
            document.getElementById('results').style.display = 'none';
        });
    }
});
    
