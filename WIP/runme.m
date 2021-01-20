function runme(filename_1)
file_dir='/Users/elysiatan/PycharmProjects/thesis/WIP/';

Train=load(strcat(file_dir,filename_1));

label_train=Train(:,1);
Train=Train(:,2:size(Train,2));

X={};
n=size(Train,1);
for i=1:n
	X{i}=Train(i,:)';
end

n=size(X,2)
m=n*20*ceil(log(n));
if (2*m>n*n)
	m=floor(n*n/2)
end
[D,Omega,d]=construct_sparse(X,n,m);
X0=zeros(n,15);
options.maxiter=20;
tic;X_train=matrix_completion_sparse_mex(D,d,Omega,X0,options);toc
Train=[label_train,X_train(1:size(Train,1),:)];
csvwrite(strcat(file_dir,'sparse_features_1.csv'),Train);


end

