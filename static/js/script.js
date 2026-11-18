// AI Shopping System Client-Side JavaScript

function fillQuery(text) {
  const input = document.getElementById('searchInput');
  if (input) {
    input.value = text;
    input.focus();
  }
}

// Comparison Selection Logic
const selectedForCompare = new Set();

function handleCompareCheck(checkbox) {
  const id = checkbox.value;
  if (checkbox.checked) {
    if (selectedForCompare.size >= 3) {
      alert("You can compare a maximum of 3 products at a time.");
      checkbox.checked = false;
      return;
    }
    selectedForCompare.add(id);
  } else {
    selectedForCompare.delete(id);
  }

  updateCompareBar();
}

function updateCompareBar() {
  const bar = document.getElementById('compareBar');
  const countSpan = document.getElementById('compareCount');
  if (!bar || !countSpan) return;

  const count = selectedForCompare.size;
  countSpan.textContent = count;

  if (count >= 1) {
    bar.style.display = 'block';
  } else {
    bar.style.display = 'none';
  }
}

function launchComparison() {
  if (selectedForCompare.size < 2) {
    alert("Please select at least 2 products to compare.");
    return;
  }
  const ids = Array.from(selectedForCompare).join(',');
  window.location.href = `/compare?ids=${ids}`;
}

