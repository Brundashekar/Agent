BEGIN {
  getline l < "encoded_file.txt"
}/attachment/{
  gsub("{attachment}",l)
}1