/// Text distance: Jaccard and Levenshtein. WASM memory at ptr.
use std::collections::HashSet;

fn tokenize(text: &str) -> Vec<&str> {
    text.split(|c:char| !c.is_alphanumeric()).filter(|s| !s.is_empty()).collect()
}

fn jaccard(t1: &[&str], t2: &[&str]) -> f64 {
    let s1: HashSet<&&str> = t1.iter().collect();
    let s2: HashSet<&&str> = t2.iter().collect();
    let inter = s1.intersection(&s2).count();
    let union = s1.union(&s2).count();
    if union == 0 { 1.0 } else { inter as f64 / union as f64 }
}

fn levenshtein(s1: &str, s2: &str) -> usize {
    let c1: Vec<char> = s1.chars().collect();
    let c2: Vec<char> = s2.chars().collect();
    let (n,m) = (c1.len(), c2.len());
    let mut dp = vec![vec![0usize; m+1]; n+1];
    for i in 0..=n { dp[i][0] = i; }
    for j in 0..=m { dp[0][j] = j; }
    for i in 1..=n { for j in 1..=m {
        dp[i][j] = (dp[i-1][j]+1).min(dp[i][j-1]+1).min(dp[i-1][j-1] + if c1[i-1]==c2[j-1]{0}else{1});
    }}
    dp[n][m]
}

fn extract_str<'a>(json: &'a str, key: &str) -> Option<&'a str> {
    let mut pos = json.find(&format!("\"{}\"", key))?;
    pos = json[pos..].find(':')? + pos + 1;
    while pos < json.len() && json.as_bytes()[pos] == b' ' { pos += 1; }
    if pos >= json.len() || json.as_bytes()[pos] != b'"' { return None; }
    pos += 1;
    let end = json[pos..].find('"')?;
    Some(&json[pos..pos+end])
}

fn write_result(ptr: *mut u8, s: &str) -> i32 {
    let b = s.as_bytes();
    unsafe { std::ptr::copy_nonoverlapping(b.as_ptr(), ptr, b.len()); }
    b.len() as i32
}

#[no_mangle]
pub extern "C" fn execute(ptr: *mut u8, len: usize) -> i32 {
    let input = unsafe { std::slice::from_raw_parts(ptr as *const u8, len) };
    let s = match std::str::from_utf8(input) { Ok(v) => v, Err(_) => return -1 };
    let t1 = extract_str(s, "text1").unwrap_or("");
    let t2 = extract_str(s, "text2").unwrap_or("");
    let metric = extract_str(s, "metric").unwrap_or("jaccard");
    let result = match metric {
        "jaccard" => {
            let tok1 = tokenize(t1); let tok2 = tokenize(t2);
            let sim = jaccard(&tok1, &tok2);
            format!("{{\"metric\":\"jaccard\",\"sim\":{:.4},\"dist\":{:.4}}}", sim, 1.0-sim)
        }
        "levenshtein" => {
            let dist = levenshtein(t1, t2);
            let mx = t1.len().max(t2.len()).max(1) as f64;
            format!("{{\"metric\":\"levenshtein\",\"dist\":{},\"sim\":{:.4}}}", dist, 1.0 - dist as f64 / mx)
        }
        _ => format!("{{\"error\":\"unknown:{}\"}}", metric),
    };
    write_result(ptr, &result)
}

fn main() {}