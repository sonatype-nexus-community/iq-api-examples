# iq-find-components
This is a sample script to search all applications that have been scanned by Lifecycle for any component using a list of packageUrls.

## Requirements
Developed for python 3 using the component requests.

## Directions
Pass in the base url to IQ Server as well as your credentials.  

```python3 ./iq-find-components.py -s https://localhost:8070 -u admin -p admin123```

List out the components to find in the included packageUrl.txt file.

```
pkg:maven/org.springframework/spring-core@*

```
The script will output the applications where the components are found to the console as well as a results.json file.  Feel free to adapt the output to your needs.

```
['sample-application', 'build', 'pkg:maven/org.springframework/spring-core@4.3.13.RELEASE?type=jar']
['struts', 'build', 'pkg:maven/org.springframework/spring-core@4.3.26.RELEASE?type=jar']

```
