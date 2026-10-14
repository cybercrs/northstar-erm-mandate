/** Exact Python string-seeded MT19937 shuffle for imported bookmarks. */
class PythonRandom {
  constructor(seed) {
    const words=[];do{words.push(Number(seed&0xffffffffn));seed>>=32n;}while(seed);
    this.mt=new Uint32Array(624);this.mt[0]=19650218;
    for(let i=1;i<624;i++)this.mt[i]=(Math.imul(1812433253,this.mt[i-1]^(this.mt[i-1]>>>30))+i)>>>0;
    let i=1,j=0;
    for(let k=Math.max(624,words.length);k>0;k--) {
      this.mt[i]=((this.mt[i]^Math.imul(this.mt[i-1]^(this.mt[i-1]>>>30),1664525))+words[j]+j)>>>0;
      if(++i>=624){this.mt[0]=this.mt[623];i=1;}if(++j>=words.length)j=0;
    }
    for(let k=623;k>0;k--) {
      this.mt[i]=((this.mt[i]^Math.imul(this.mt[i-1]^(this.mt[i-1]>>>30),1566083941))-i)>>>0;
      if(++i>=624){this.mt[0]=this.mt[623];i=1;}
    }
    this.mt[0]=0x80000000;this.index=624;
  }
  next() {
    if(this.index>=624) {
      for(let i=0;i<624;i++) {
        const value=(this.mt[i]&0x80000000)|(this.mt[(i+1)%624]&0x7fffffff);
        this.mt[i]=(this.mt[(i+397)%624]^(value>>>1)^((value&1)?0x9908b0df:0))>>>0;
      }
      this.index=0;
    }
    let value=this.mt[this.index++];value^=value>>>11;value^=(value<<7)&0x9d2c5680;value^=(value<<15)&0xefc60000;value^=value>>>18;
    return value>>>0;
  }
  below(n) {const bits=n.toString(2).length;let value;do{value=this.next()>>>(32-bits);}while(value>=n);return value;}
}

// CPython v2 string seeding uses the UTF-8 seed bytes followed by SHA-512.
export async function shuffled(input, seed, field) {
  const text = new TextEncoder().encode(`${seed}:${field}`);
  const digest = new Uint8Array(await crypto.subtle.digest('SHA-512', text));
  let number = 0n;
  for (const byte of [...text, ...digest]) number = (number << 8n) | BigInt(byte);
  const random = new PythonRandom(number), result = [...input];
  for (let i = result.length - 1; i > 0; i--) {
    const j = random.below(i + 1); [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}
