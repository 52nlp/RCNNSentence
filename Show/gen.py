import cPickle
import sys

framwork1='''<!DOCTYPE HTML>
<html>
	<head>
		<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
		<title>Result</title>

		<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.8.2/jquery.min.js"></script>
		<style type="text/css">
${demo.css}
		</style>
		<script type="text/javascript">
$(function () {
    $('#container1').highcharts({
        chart: {
            type: 'spline'
        },
        title: {
            text: 'Accuracy in Train/Val/Test Set'
        },
        subtitle: {
            text: '%s'
        },
        xAxis: {
            title: {
                text: 'Epoch'
            }
        },
        yAxis: {
            title: {
                text: 'Accuracy (%%)'
            },
        },
        tooltip: {
            headerFormat: '<b>{series.name}</b><br>',
            pointFormat: '{point.x: .2f}: {point.y:.2f} %%'
        },

        plotOptions: {
            spline: {
                marker: {
                    enabled: true
                }
            }
        },
'''

framwork2='''
   });
});
		</script>
<script type="text/javascript">
$(function () {
    $('#container2').highcharts({
        chart: {
            zoomType: 'x'
        },
        title: {
            text: 'Value of Loss Function'
        },
        subtitle: {},
        xAxis: {
            title:{
                text: 'Epoch'
            },
            minRange: %f
        },
        yAxis: {
            title: {
                text: 'Value'
            }
        },
        legend: {
            enabled: false
        },
        plotOptions: {
            area: {
                fillColor: {
                    linearGradient: { x1: 0, y1: 0, x2: 0, y2: 1},
                    stops: [
                        [0, Highcharts.getOptions().colors[0]],
                        [1, Highcharts.Color(Highcharts.getOptions().colors[0]).setOpacity(0).get('rgba')]
                    ]
                },
                marker: {
                    radius: 2
                },
                lineWidth: 1,
                states: {
                    hover: {
                        lineWidth: 1
                    }
                },
                threshold: null
            }
        },

        series: [{
            type: 'area',
            name: 'Value',
            pointInterval: %f,
            pointStart: 0,
            data: [
'''
framwork3='''
            ]
        }]
    });
});
          </script>

	</head>
	<body>
<script src="../js/highcharts.js"></script>
<script src="../js/modules/exporting.js"></script>

<div id="container1" style="min-width: 310px; height: 800px; margin: 0 auto"></div>
<div id="container2" style="min-width: 310px; height: 800px; margin: 0 auto"></div>

	</body>
</html>
'''

if __name__=='__main__':
	if len(sys.argv)!=2 and len(sys.argv)!=3:
		print 'Usage: python gen.py <inputfile>'
		print 'Usage: python gen.py <inputfile> <outputfile>'
		exit(0)

	fileName=sys.argv[1]
	try:
		index=fileName.find('__')
		index=len(fileName) if index<0 else index
		dirNum=fileName.count('/')
		if dirNum==0:
			sp=-1
		else:
			sp=0
			for i in xrange(dirNum):
				sp=fileName.find('/',sp+1)
		sp0=fileName.find('_',sp+1)
		sp1=fileName.find('_',sp0+1)
		sp2=fileName.find('_',sp1+1)
		month=int(fileName[sp+1:sp0])
		day=int(fileName[sp0+1:sp1])
		hour=int(fileName[sp1+1:sp2])
		minute=int(fileName[sp2+1:index])
		if len(sys.argv)==2:
			outFileName='./charts/'+fileName[sp+1:index]+'.htm'
		else:
			outFileName='./charts/'+sys.argv[2]
	except:
		month=day=hour=minute=0
		name=fileName
		while name.find('/')>=0:
			sp=name.find('/')
			name=name[sp+1:]
		outFileName='./charts/'+name+'.htm'

	data=cPickle.load(open(fileName,'rb'))
	result=data[0];costValue=data[4]
	trainAcc=data[1];validateAcc=data[2];testAcc=data[3]

	finalAcc=round(result['finalAcc']*100.,2)
	bestValAcc=round(result['bestValAcc']*100.,2)
	bestTestAcc=round((1-result['minError'])*100.,2)

	subtitle='%i/%i %i:%i, Final: %f%%, BestVal: %f%% BestTest: %f%%'%(
		month,day,hour,minute,finalAcc,bestValAcc,bestTestAcc)
	print subtitle

	with open(outFileName,'w') as fopen:
		fopen.write(framwork1%subtitle)
		fopen.write('''
        series: [{
          name:'TrainAcc',
          data:[
		''')
		for i in xrange(len(trainAcc)):
			if i+1!=len(trainAcc):
				fopen.write('          ['+str(trainAcc[i]['x'])+', '+str(trainAcc[i]['acc']*100.)+'],\n')
			else:
				fopen.write('          ['+str(trainAcc[i]['x'])+', '+str(trainAcc[i]['acc']*100.)+']\n')
		fopen.write('''
          ]
        }, {
          name:'ValAcc',
          data:[
			''')
		for i in xrange(len(validateAcc)):
			if i+1!=len(validateAcc):
				fopen.write('          ['+str(validateAcc[i]['x'])+', '+str(validateAcc[i]['acc']*100.)+'],\n')
			else:
				fopen.write('          ['+str(validateAcc[i]['x'])+', '+str(validateAcc[i]['acc']*100.)+']\n')
		fopen.write('''
          ]
        }, {
          name:'TestAcc',
          data:[
			''')
		for i in xrange(len(testAcc)):
			if i+1!=len(testAcc):
				fopen.write('          ['+str(testAcc[i]['x'])+', '+str(testAcc[i]['acc']*100.)+'],\n')
			else:
				fopen.write('          ['+str(testAcc[i]['x'])+', '+str(testAcc[i]['acc']*100.)+']\n')
		fopen.write('''
          ]
        }]
			''')
		minInterval=costValue[1]['x']-costValue[0]['x']
		fopen.write(framwork2%(minInterval,minInterval))
		for i in xrange(len(costValue)):
			if i+1==len(costValue):
				fopen.write(str(costValue[i]['value'])+'\n')
			else:
				fopen.write(str(costValue[i]['value'])+',')
			if i%100==0:
				fopen.write('\n\t')
		fopen.write(framwork3)
