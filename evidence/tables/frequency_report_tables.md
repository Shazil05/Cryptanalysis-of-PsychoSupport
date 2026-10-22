# Frequency Analysis & Preprocessing Tables

## 1. Ciphertext Summary & Index of Coincidence (IC)

| id   | direction      | username   |   mood |   raw_len |   clean_len |        ic | top_5_cipher_letters                           |
|:-----|:---------------|:-----------|-------:|----------:|------------:|----------:|:-----------------------------------------------|
| C1   | Client->Server | Alex       |      1 |       186 |         184 | 0.161262  | U: 34.8%, X: 11.4%, I: 9.2%, R: 8.7%, C: 7.6%  |
| S1   | Server->Client | Alex       |      1 |       876 |         728 | 0.0672869 | O: 13.6%, H: 9.9%, A: 8.2%, C: 8.2%, P: 7.6%   |
| C2   | Client->Server | Brenda     |      2 |       172 |         170 | 0.133658  | I: 27.6%, N: 17.1%, O: 10.6%, E: 7.6%, D: 6.5% |
| S2   | Server->Client | Brenda     |      2 |       147 |         124 | 0.0587464 | E: 11.3%, Y: 10.5%, W: 8.9%, S: 8.1%, O: 6.5%  |
| C3   | Client->Server | Charlie    |      3 |       184 |         182 | 0.147532  | W: 29.7%, D: 17.6%, U: 11.0%, G: 7.1%, P: 6.0% |
| S3   | Server->Client | Charlie    |      3 |       951 |         791 | 0.0641457 | I: 11.9%, K: 9.0%, J: 8.7%, G: 8.2%, T: 6.8%   |
| C4   | Client->Server | Diana      |      4 |       182 |         180 | 0.153197  | K: 31.1%, T: 16.7%, A: 10.6%, I: 8.3%, B: 7.2% |
| S4   | Server->Client | Diana      |      4 |       946 |         786 | 0.06161   | S: 11.3%, I: 8.1%, C: 8.0%, V: 7.5%, E: 7.4%   |
| C5   | Client->Server | Ethan      |      5 |       182 |         180 | 0.147052  | Y: 31.7%, J: 13.3%, G: 11.1%, K: 7.2%, I: 6.1% |
| S5   | Server->Client | Ethan      |      5 |       913 |         754 | 0.067641  | C: 12.6%, K: 10.1%, L: 9.4%, X: 7.7%, U: 7.4%  |
| C6   | Client->Server | Fiona      |      6 |       180 |         178 | 0.134641  | Y: 28.1%, N: 16.9%, Q: 9.6%, M: 9.0%, U: 5.6%  |
| S6   | Server->Client | Fiona      |      6 |       941 |         776 | 0.0684237 | U: 12.0%, C: 10.7%, Z: 8.8%, L: 8.1%, W: 8.1%  |
| C7   | Client->Server | George     |      7 |       184 |         182 | 0.142189  | A: 28.0%, P: 18.1%, S: 10.4%, L: 8.2%, O: 6.6% |
| S7   | Server->Client | George     |      7 |       919 |         759 | 0.0690083 | W: 14.2%, O: 8.8%, N: 8.4%, E: 8.2%, B: 7.9%   |
| C8   | Client->Server | Hannah     |      8 |       188 |         186 | 0.149143  | O: 32.3%, F: 13.4%, Y: 10.2%, Q: 7.5%, G: 5.9% |
| S8   | Server->Client | Hannah     |      8 |       992 |         825 | 0.0624595 | G: 9.6%, B: 9.2%, U: 9.2%, Q: 8.8%, W: 8.2%    |
| C9   | Client->Server | Ian        |      9 |       184 |         182 | 0.153421  | C: 31.3%, V: 18.1%, E: 9.3%, J: 7.7%, S: 6.6%  |
| S9   | Server->Client | Ian        |      9 |       891 |         728 | 0.0688816 | Q: 13.9%, P: 8.9%, S: 8.8%, O: 8.4%, F: 7.7%   |
| C10  | Client->Server | Julia      |     10 |       182 |         180 | 0.151024  | Q: 33.3%, K: 11.1%, L: 10.0%, U: 7.8%, V: 6.7% |
| S10  | Server->Client | Julia      |     10 |       944 |         785 | 0.0670935 | A: 14.0%, U: 8.4%, H: 7.9%, I: 7.9%, D: 7.6%   |

## 2. Directional Characteristics

- **Client->Server (Armored Hex Nibbles + Affine)**: Mean IC = 0.1473, Letters restricted to 16-character subset.
- **Server->Client (Natural English Advice + Affine)**: Mean IC = 0.0655, Natural English monoalphabetic distribution.
