/// Matrix multiply NxM * MxK → NxK. WASM memory at ptr.
fn write_result(ptr: *mut u8, s: &str) -> i32 {
    let b = s.as_bytes();
    unsafe { std::ptr::copy_nonoverlapping(b.as_ptr(), ptr, b.len()); }
    b.len() as i32
}

#[no_mangle]
pub extern "C" fn execute(ptr: *mut u8, len: usize) -> i32 {
    let input = unsafe { std::slice::from_raw_parts(ptr as *const u8, len) };
    let s = match std::str::from_utf8(input) { Ok(v) => v, Err(_) => return -1 };
    // Parse [[a11,a12],[a21,a22]] and [[b11,b12],[b21,b22]] from JSON
    let a = parse_matrix(s, "a");
    let b = parse_matrix(s, "b");
    if a.is_empty() || b.is_empty() { return write_result(ptr, "{\"error\":\"empty\"}"); }
    let n = a.len(); let p = a[0].len();
    if p != b.len() { return write_result(ptr, &format!("{{\"error\":\"dim mismatch: {}x{} * {}x{}\"}}", n,p,b.len(),b[0].len())); }
    let m = b[0].len();
    let mut result = String::from("[");
    for i in 0..n {
        if i > 0 { result.push(','); }
        result.push('[');
        for j in 0..m {
            if j > 0 { result.push(','); }
            let mut sum = 0.0f64;
            for k in 0..p { sum += a[i][k] * b[k][j]; }
            result.push_str(&format!("{}", sum));
        }
        result.push(']');
    }
    result.push(']');
    write_result(ptr, &format!("{{\"result\":{}}}", result))
}

fn parse_matrix(s: &str, key: &str) -> Vec<Vec<f64>> {
    let mut pos = match s.find(&format!("\"{}\"", key)) { Some(p) => p, None => return vec![] };
    pos = match s[pos..].find(':') { Some(p) => pos + p + 1, None => return vec![] };
    while pos < s.len() && s.as_bytes()[pos] == b' ' { pos += 1; }
    let rest = &s[pos..];
    let start = match rest.find("[[") { Some(p) => pos + p, None => return vec![] };
    let mut depth = 0u32;
    let mut end = start;
    for (i, ch) in s[start..].char_indices() {
        if ch == '[' { depth += 1; } else if ch == ']' { depth -= 1; if depth == 0 { end = start + i + 1; break; } }
    }
    let matrix_str = &s[start..end];
    // Remove outer brackets and split by "], [" or "],["
    let inner = matrix_str.trim_start_matches('[').trim_end_matches(']').trim();
    if inner.is_empty() { return vec![]; }
    let rows: Vec<&str> = inner.split("], [").flat_map(|r| r.split("],[")).collect();
    rows.iter().map(|row| {
        row.split(',').filter_map(|v| v.trim().parse::<f64>().ok()).collect()
    }).filter(|r: &Vec<f64>| !r.is_empty()).collect()
}

fn main() {}